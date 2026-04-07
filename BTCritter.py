import asyncio
import random
import py_trees as pt
from py_trees import common
import Goals_BT_Basic
import Sensors

# ==========================================
# 1. ROAMING & OBSTACLE AVOIDANCE (Reused from BTRoam)
# ==========================================

class BN_ForwardRandom(pt.behaviour.Behaviour):
    def __init__(self, aagent):
        self.my_goal = None
        super(BN_ForwardRandom, self).__init__("BN_ForwardRandom")
        self.my_agent = aagent

    def initialise(self):
        self.my_goal = asyncio.create_task(Goals_BT_Basic.ForwardDist(self.my_agent, -1, 1, 5).run())

    def update(self):
        if not self.my_goal.done():
            return pt.common.Status.RUNNING
        return pt.common.Status.SUCCESS if self.my_goal.result() else pt.common.Status.FAILURE

    def terminate(self, new_status: common.Status):
        if self.my_goal: self.my_goal.cancel()


class BN_TurnRandom(pt.behaviour.Behaviour):
    def __init__(self, aagent):
        self.my_goal = None
        super(BN_TurnRandom, self).__init__("BN_TurnRandom")
        self.my_agent = aagent

    def initialise(self):
        self.my_goal = asyncio.create_task(Goals_BT_Basic.Turn(self.my_agent).run())

    def update(self):
        if not self.my_goal.done():
            return pt.common.Status.RUNNING
        return pt.common.Status.SUCCESS if self.my_goal.result() else pt.common.Status.FAILURE

    def terminate(self, new_status: common.Status):
        if self.my_goal: self.my_goal.cancel()


class BN_ObstacleAhead(pt.behaviour.Behaviour):
    def __init__(self, aagent):
        super(BN_ObstacleAhead, self).__init__("BN_ObstacleAhead")
        self.my_agent = aagent

    def update(self):
        sensor_obj_info = self.my_agent.rc_sensor.sensor_rays[Sensors.RayCastSensor.OBJECT_INFO]
        for index in [1, 2, 3]:
            hit = sensor_obj_info[index]
            # ADDED 'AlienFlower' and 'CritterManta Ray' TO THE OBSTACLE LIST!
            if hit and hit.get("tag") in ["Wall", "Rock", "AlienFlower", "CritterManta Ray","Container"]:
                return pt.common.Status.SUCCESS
        return pt.common.Status.FAILURE


# ==========================================
# 2. CRITTER-SPECIFIC CONDITIONS
# ==========================================

class BN_DetectAstronaut(pt.behaviour.Behaviour):
    def __init__(self, aagent):
        super().__init__("BN_DetectAstronaut")
        self.my_agent = aagent
        self.my_agent.astronaut_dist = 999
        self.my_agent.astronaut_dir = None

    def update(self):
        sensor_obj_info = self.my_agent.rc_sensor.sensor_rays[Sensors.RayCastSensor.OBJECT_INFO]
        center_ray = len(sensor_obj_info) // 2

        astro_hits = []
        for index, value in enumerate(sensor_obj_info):
            if value and value.get("tag") == "Astronaut":
                # Get the actual distance in Unity meters
                dist = value.get("distance", value.get("distanceFraction", 999))
                astro_hits.append((index, dist))

        if not astro_hits:
            # BLINDSPOT FIX: If we suddenly lose sight, but we were practically touching...
            if getattr(self.my_agent, "astronaut_dist", 999) <= 2.0:
                # We probably bumped into her! Fake a very close distance to force the bite!
                self.my_agent.astronaut_dist = 0.1 
                return pt.common.Status.SUCCESS

            # Otherwise, we genuinely lost sight of her.
            self.my_agent.astronaut_dir = None
            self.my_agent.astronaut_dist = 999
            return pt.common.Status.FAILURE

        # Prioritize the astronaut closest to the center ray
        astro_hits.sort(key=lambda x: abs(x[0] - center_ray))
        best_ray, best_dist = astro_hits[0]

        if best_ray < center_ray:
            self.my_agent.astronaut_dir = "left"
        elif best_ray > center_ray:
            self.my_agent.astronaut_dir = "right"
        else:
            self.my_agent.astronaut_dir = "center"

        self.my_agent.astronaut_dist = best_dist
        return pt.common.Status.SUCCESS


class BN_CloseToAstronaut(pt.behaviour.Behaviour):
    def __init__(self, aagent):
        super().__init__("BN_CloseToAstronaut")
        self.my_agent = aagent

    def update(self):
        dist = getattr(self.my_agent, "astronaut_dist", 999)
        
        # 1.5 Unity units means their colliders have successfully bumped into each other
        if dist <= 1.5:
            return pt.common.Status.SUCCESS
            
        return pt.common.Status.FAILURE
    

# ==========================================
# 3. CRITTER-SPECIFIC ACTIONS
# ==========================================

class BN_ApproachAstronaut(pt.behaviour.Behaviour):
    def __init__(self, aagent):
        super().__init__("BN_ApproachAstronaut")
        self.my_agent = aagent
        self.current_cmd = None
        self.move_task = None

    def initialise(self):
        self.current_cmd = None

    def update(self):
        direction = getattr(self.my_agent, "astronaut_dir", None)
        if direction is None:
            return pt.common.Status.FAILURE

        desired_cmd = "mf" if direction == "center" else ("tl" if direction == "left" else "tr")

        if self.current_cmd != desired_cmd:
            if self.move_task and not self.move_task.done():
                self.move_task.cancel()
            self.move_task = asyncio.create_task(self.send_safe_movement(desired_cmd))
            self.current_cmd = desired_cmd

        return pt.common.Status.RUNNING

    async def send_safe_movement(self, cmd):
        await asyncio.sleep(0.1)
        await self.my_agent.send_message("action", "stop")
        await self.my_agent.send_message("action", "nt")
        await self.my_agent.send_message("action", cmd)

    def terminate(self, new_status: pt.common.Status):
        if self.move_task and not self.move_task.done():
            self.move_task.cancel()


class BN_Retreat(pt.behaviour.Behaviour):
    def __init__(self, aagent):
        super().__init__("BN_Retreat")
        self.my_agent = aagent
        self.retreat_task = None

    def initialise(self):
        if self.retreat_task and not self.retreat_task.done():
            self.retreat_task.cancel()
        self.retreat_task = asyncio.create_task(self.do_retreat())

    async def do_retreat(self):
        # 1. Stop attacking
        await self.my_agent.send_message("action", "stop")
        await self.my_agent.send_message("action", "nt")
        await asyncio.sleep(0.1)
        # 2. Turn around
        await self.my_agent.send_message("action", "tr")
        await asyncio.sleep(1.0)
        # 3. Run away
        await self.my_agent.send_message("action", "nt")
        await self.my_agent.send_message("action", "mf")
        await asyncio.sleep(2.0)
        await self.my_agent.send_message("action", "stop")

    def update(self):
        if self.retreat_task and not self.retreat_task.done():
            return pt.common.Status.RUNNING
        return pt.common.Status.SUCCESS
        
    def terminate(self, new_status):
        if self.retreat_task and not self.retreat_task.done():
            self.retreat_task.cancel()


# ==========================================
# 4. THE CRITTER BEHAVIOR TREE
# ==========================================

class BTCritter:
    def __init__(self, aagent):
        self.aagent = aagent

        # PRIORITY 1: RETREAT AFTER BITING
        retreat_seq = pt.composites.Sequence(name="Retreat Sequence", memory=True)
        retreat_seq.add_children([
            BN_DetectAstronaut(aagent),   
            BN_CloseToAstronaut(aagent),  
            BN_Retreat(aagent)            
        ])

        # PRIORITY 2: ATTACK
        attack_seq = pt.composites.Sequence(name="Attack Sequence", memory=False)
        attack_seq.add_children([
            BN_DetectAstronaut(aagent),    
            BN_ApproachAstronaut(aagent)  
        ])

        # PRIORITY 3: SAFE ROAMING
        avoid_obstacle_seq = pt.composites.Sequence(name="Avoid Obstacle", memory=False)
        avoid_obstacle_seq.add_children([
            BN_ObstacleAhead(aagent),  
            BN_TurnRandom(aagent)      
        ])

        roam_sequence = pt.composites.Sequence(name="Roam", memory=True)
        roam_sequence.add_children([
            BN_ForwardRandom(aagent),   
            BN_TurnRandom(aagent)
        ])

        safe_roam_selector = pt.composites.Selector(name="Safe Roam Selector", memory=False)
        safe_roam_selector.add_children([
            avoid_obstacle_seq, 
            roam_sequence       
        ])

        # ROOT
        self.root = pt.composites.Selector(name="Critter Root", memory=False)
        self.root.add_children([
            retreat_seq,      
            attack_seq,     
            safe_roam_selector
        ])

        self.behaviour_tree = pt.trees.BehaviourTree(self.root)

    def stop_behaviour_tree(self):
        self.root.tick_once()
        for node in self.root.iterate():
            if node.status != pt.common.Status.INVALID:
                node.status = pt.common.Status.INVALID
                if hasattr(node, "terminate"):
                    node.terminate(pt.common.Status.INVALID)

    async def tick(self):
        self.behaviour_tree.tick()
        await asyncio.sleep(0)