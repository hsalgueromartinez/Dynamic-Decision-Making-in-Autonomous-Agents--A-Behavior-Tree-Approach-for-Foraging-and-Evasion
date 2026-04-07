import asyncio
import random
import py_trees as pt
from py_trees import common
import Goals_BT_Basic
import Sensors

# ==========================================
# BASIC MOTION BEHAVIORS
# ==========================================

class BN_DoNothing(pt.behaviour.Behaviour):
    def __init__(self, aagent):
        self.my_agent = aagent
        self.my_goal = None
        super(BN_DoNothing, self).__init__("BN_DoNothing")

    def initialise(self):
        self.my_goal = asyncio.create_task(Goals_BT_Basic.DoNothing(self.my_agent).run())

    def update(self):
        if not self.my_goal.done():
            return pt.common.Status.RUNNING
        else:
            if self.my_goal.result():
                return pt.common.Status.SUCCESS
            else:
                return pt.common.Status.FAILURE

    def terminate(self, new_status: common.Status):
        if self.my_goal: self.my_goal.cancel()


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
        else:
            if self.my_goal.result():
                return pt.common.Status.SUCCESS
            else:
                return pt.common.Status.FAILURE

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
        else:
            res = self.my_goal.result()
            if res:
                return pt.common.Status.SUCCESS
            else:
                return pt.common.Status.FAILURE

    def terminate(self, new_status: common.Status):
        if self.my_goal: self.my_goal.cancel()


# ==========================================
# CUSTOM CONDITIONS
# ==========================================

# REQUIRED FROZEN CONDITION
class BN_DetectFrozen(pt.behaviour.Behaviour):
    def __init__(self, aagent):
        self.my_goal = None
        super(BN_DetectFrozen, self).__init__("BN_DetectFrozen")
        self.my_agent = aagent
        self.i_state = aagent.i_state

    def initialise(self):
        pass

    def update(self):
        if self.i_state.isFrozen:
            return pt.common.Status.SUCCESS
        return pt.common.Status.FAILURE

    def terminate(self, new_status: common.Status):
        pass


#we have added a helper method on the AAgent class that counts the number of flowers in the inventory
class BN_IsInventoryFull(pt.behaviour.Behaviour):
    def __init__(self, aagent):
        super(BN_IsInventoryFull, self).__init__("BN_IsInventoryFull")
        self.my_agent = aagent

    def update(self):
        if self.my_agent.count_alien_flowers() >= 2:
            return pt.common.Status.SUCCESS
        return pt.common.Status.FAILURE  


class BN_IsAtBase(pt.behaviour.Behaviour):
    def __init__(self, aagent):
        super(BN_IsAtBase, self).__init__("BN_IsAtBase")
        self.my_agent = aagent

    def update(self):
        if self.my_agent.i_state.nearbyContainerInventory:
            return pt.common.Status.SUCCESS
        return pt.common.Status.FAILURE
    

#PART 3: we use a helper function from the AAgent class, and use the dictionary containing the distance from the agent to the critter to determine wether he is too close to the thread. (too close is defined with a threshold)
class BN_CritterTooClose(pt.behaviour.Behaviour):
    def __init__(self, aagent, threshold=2.5):
        super(BN_CritterTooClose, self).__init__("BN_CritterTooClose")
        self.my_agent = aagent
        self.threshold = threshold

    def update(self):
        self.my_agent.detect_critter_direction()
        if getattr(self.my_agent, "critter_dist", 999) <= self.threshold:
            return pt.common.Status.SUCCESS
        return pt.common.Status.FAILURE


# ==========================================
# CUSTOM ACTIONS
# ==========================================

#For improving the roam behavior
class BN_ObstacleAhead(pt.behaviour.Behaviour):
    def __init__(self, aagent):
        super(BN_ObstacleAhead, self).__init__("BN_ObstacleAhead")
        self.my_agent = aagent

    def update(self):
        # Get the objects currently seen by the raycast sensors
        sensor_obj_info = self.my_agent.rc_sensor.sensor_rays[Sensors.RayCastSensor.OBJECT_INFO]
        
        # Check the 3 middle rays (Index 1, 2, and 3)
        for index in [1, 2, 3]:
            hit = sensor_obj_info[index]
            # If any of these rays see a Rock or a Wall: trigger avoidance
            if hit and hit.get("tag") in ["Wall", "Rock", "Container", "CritterMantaRay"]:
                return pt.common.Status.SUCCESS
                
        return pt.common.Status.FAILURE
    

class BN_WalkToBase(pt.behaviour.Behaviour):
    def __init__(self, aagent):
        super(BN_WalkToBase, self).__init__("BN_WalkToBase")
        self.my_agent = aagent
        self.walk_task = None

    def initialise(self):
        # This kills the leftover momentum from BN_ApproachFlower
        asyncio.create_task(self.my_agent.send_message("action", "stop"))
        asyncio.create_task(self.my_agent.send_message("action", "nt"))
        
        self.walk_task = asyncio.create_task(self.delayed_walk())

    async def delayed_walk(self):
        # Give Unity 0.5 seconds to completely halt the astronaut's physics
        await asyncio.sleep(0.5) 
        await self.my_agent.send_message("action", "walk_to,BaseAlpha")

    def update(self):
        # Check if we successfully arrived at the base container
        if self.my_agent.i_state.nearbyContainerInventory:
            return pt.common.Status.SUCCESS
            
        return pt.common.Status.RUNNING

    def terminate(self, new_status: pt.common.Status):
        if self.walk_task and not self.walk_task.done():
            self.walk_task.cancel()


class BN_LeaveFlowers(pt.behaviour.Behaviour):
    def __init__(self, aagent):
        super(BN_LeaveFlowers, self).__init__("BN_LeaveFlowers")
        self.my_agent = aagent
        self.my_goal = None
        self.sent = False

    def initialise(self):
        self.sent = False
        self.my_goal = None

    def update(self):
        has_flowers = self.my_agent.count_alien_flowers() > 0

        if not has_flowers:
            return pt.common.Status.SUCCESS #means that the flowers have been deposited
        
        if not self.my_agent.i_state.nearbyContainerInventory:
            return pt.common.Status.FAILURE

        #if there are still flowers in the inventory, trigger the action
        if not self.sent:
            amount = self.my_agent.count_alien_flowers()
            self.my_goal = asyncio.create_task(
                self.my_agent.send_message("action", f"leave,AlienFlower,{amount}")
            )
            self.sent = True

        return pt.common.Status.RUNNING
    
    def terminate(self, new_status: pt.common.Status):
        if self.my_goal and not self.my_goal.done():
            self.my_goal.cancel()


# Helper function to detect the flower direction inside the AAgent class
class BN_DetectFlower(pt.behaviour.Behaviour):
    def __init__(self, aagent):
        super(BN_DetectFlower, self).__init__("BN_DetectFlower")
        self.my_agent = aagent

    def update(self):
        direction = self.my_agent.detect_flower_direction()

        if direction is None:
            return pt.common.Status.FAILURE

        self.my_agent.flower_dir = direction
        return pt.common.Status.SUCCESS
    

#In case the flower counter increases, this means the flower has been collected. If the flower is no longer detected and the counter does not increase, this means the agent was walked away from the flower
class BN_ApproachFlower(pt.behaviour.Behaviour):
    def __init__(self, aagent):
        super(BN_ApproachFlower, self).__init__("BN_ApproachFlower")
        self.my_agent = aagent
        self.current_cmd = None
        self.start_flower_count = 0
        self.move_task = None

    def initialise(self):
        # Reset the command tracker when we start a new approach
        self.current_cmd = None
        self.start_flower_count = self.my_agent.count_alien_flowers()

    def update(self):
        direction = self.my_agent.detect_flower_direction()
        current_count = self.my_agent.count_alien_flowers()

        # Did we lose the flower?
        if direction is None:
            # Check if we successfully picked it up
            if current_count > self.start_flower_count:
                return pt.common.Status.SUCCESS
            else:
                return pt.common.Status.FAILURE

        # Determine the steering command
        if direction == "left":
            desired_cmd = "tl"
        elif direction == "right":
            desired_cmd = "tr"
        else:
            desired_cmd = "mf"

        # If the command changed, send it
        if self.current_cmd != desired_cmd:
            # Cancel any previous delayed movement tasks to prevent overlaps
            if self.move_task and not self.move_task.done():
                self.move_task.cancel()
                
            self.move_task = asyncio.create_task(self.send_safe_movement(desired_cmd))
            self.current_cmd = desired_cmd

        return pt.common.Status.RUNNING

    async def send_safe_movement(self, cmd):
        #Wait 0.1 seconds to let any canceled roaming tasks send their "stop" commands
        await asyncio.sleep(0.1)
        
        #Clear out any residual turning states
        await self.my_agent.send_message("action", "stop")
        await self.my_agent.send_message("action", "nt")
        
        #Send the actual command to approach the flower
        await self.my_agent.send_message("action", cmd)

    def terminate(self, new_status: pt.common.Status):
        if self.move_task and not self.move_task.done():
            self.move_task.cancel()


# 3RD PART: just check wether there is a critter inside the agent's perception field
class BN_DetectCritter(pt.behaviour.Behaviour):
    def __init__(self, aagent):
        super(BN_DetectCritter, self).__init__("BN_DetectCritter")
        self.my_agent = aagent

    def update(self):
        direction = self.my_agent.detect_critter_direction()
        if direction is None:
            return pt.common.Status.FAILURE
        return pt.common.Status.SUCCESS


# 3RD PART: main action in which the agent avoids the critter
class BN_EvadeCritter(pt.behaviour.Behaviour):
    def __init__(self, aagent):
        super(BN_EvadeCritter, self).__init__("BN_EvadeCritter")
        self.my_agent = aagent
        self.evade_task = None

    def initialise(self):
        self.evade_task = asyncio.create_task(self.do_evade())

    async def do_evade(self):
        direction = getattr(self.my_agent, "critter_dir", None)

        await self.my_agent.send_message("action", "stop")
        await self.my_agent.send_message("action", "nt")
        await asyncio.sleep(0.1)

        if direction == "left":
            await self.my_agent.send_message("action", "tr")
        elif direction == "right":
            await self.my_agent.send_message("action", "tl")
        else:
            await self.my_agent.send_message("action", random.choice(["tl", "tr"]))

        await asyncio.sleep(0.8)
        await self.my_agent.send_message("action", "nt")
        await self.my_agent.send_message("action", "mf")
        await asyncio.sleep(1.2)
        await self.my_agent.send_message("action", "ntm")

    def update(self):
        if self.evade_task and not self.evade_task.done():
            return pt.common.Status.RUNNING
        return pt.common.Status.SUCCESS

    def terminate(self, new_status: pt.common.Status):
        if self.evade_task and not self.evade_task.done():
            self.evade_task.cancel()


class BN_StopMovement(pt.behaviour.Behaviour):
    def __init__(self, aagent):
        super(BN_StopMovement, self).__init__("BN_StopMovement")
        self.my_agent = aagent
        self.my_goal_move = None
        self.my_goal_turn = None

    def initialise(self):
        self.my_goal_move = asyncio.create_task(self.my_agent.send_message("action", "stop"))
        self.my_goal_turn = asyncio.create_task(self.my_agent.send_message("action", "nt"))

    def update(self):
        return pt.common.Status.SUCCESS


# ==========================================
# FINAL PPA TREE FOR "SCENARIO ALONE"
# ==========================================

#3RD PART: specific tree that incorporates the critter avoidance by the agent
class BTAvoid:
    def __init__(self, aagent):
        self.aagent = aagent

        frozen_seq = pt.composites.Sequence(name="Frozen Sequence", memory=False)
        frozen_seq.add_children([
            BN_DetectFrozen(aagent),
            BN_DoNothing(aagent)
        ])

        #this is the new branch, which recieves maximum priority after the frozen sequence. It basically detects wether the critter is in the agent perception field, concretely wether it is too close to the agent, and then calls the avoidance actuator
        evade_seq = pt.composites.Sequence(name="Evade Critter", memory=False)
        evade_seq.add_children([
            BN_DetectCritter(aagent),
            BN_CritterTooClose(aagent, threshold=2.5),
            BN_EvadeCritter(aagent)
        ])

        leave_seq = pt.composites.Sequence(name="Leave Flowers", memory=False)
        leave_seq.add_children([
            BN_IsAtBase(aagent),
            BN_LeaveFlowers(aagent)
        ])

        walk_to_base_seq = pt.composites.Sequence(name="Walk to Base", memory=False)
        walk_to_base_seq.add_children([
            BN_WalkToBase(aagent)
        ])

        deposit_selector = pt.composites.Selector(name="Deposit Selector", memory=False)
        deposit_selector.add_children([
            leave_seq,
            walk_to_base_seq
        ])

        manage_inventory_seq = pt.composites.Sequence(name="Manage Inventory", memory=False)
        manage_inventory_seq.add_children([
            BN_IsInventoryFull(aagent),
            deposit_selector
        ])

        approach_seq = pt.composites.Sequence(name="Approach Flower", memory=False)
        approach_seq.add_children([
            BN_DetectFlower(aagent),
            BN_ApproachFlower(aagent)
        ])

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

        harvest_selector = pt.composites.Selector(name="Harvest Selector", memory=False)
        harvest_selector.add_children([
            approach_seq,
            safe_roam_selector
        ])

        autonomous_logic = pt.composites.Selector(name="Autonomous Logic", memory=False)
        autonomous_logic.add_children([
            evade_seq,
            manage_inventory_seq,
            harvest_selector
        ])

        self.root = pt.composites.Selector(name="Root Selector", memory=False)
        self.root.add_children([
            frozen_seq,
            autonomous_logic
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