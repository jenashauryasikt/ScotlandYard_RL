from utilities import *
import numpy as np
import random
from utilities import detective,graph_utils,MrX,observation
class game:
    def __init__(self,n=4):
        self.board = graph_utils.graph()
        self.no_of_players = n
        positions = self.board.initial_pos(n+1)
        # M is a set , use like for x in M:
        self.M={13,26,29,34,50,53,91,94,103,112,117,132,138,141,155,174,197,198}
        self.f_x = np.zeros((200))
        self.f_d = np.zeros((200))
        self.X = MrX.MrX()
        self.detectives = [detective.detective(i) for i in range(0,n)]
        for k in range(1,n+1):
            self.M.remove(positions[k])
        self.X.set_position(positions[0])
        for i in range(1,n+1):
            self.detectives[i-1].set_position(positions[i])

        self.end_flag = False
        self.move = 0

        self.observation = observation.observation()
        self.X_reward=0
        self.D_reward=0
        return

    def finish(self):
        if(self.end_flag):
            return self.end_flag
        if(len(self.list_of_action_x()) == 0 or self.list_of_action_x().keys()==[4]):
            self.end_flag = True
            self.X_reward-=10
            self.D_reward+=10
            return True

        if(self.move >= 20):
            self.end_flag = True
            self.X_reward+=10
            self.D_reward+=-10
            return self.end_flag

        for i in range(1,self.no_of_players):

            if(self.X.position == self.detectives[i].position):
                self.end_flag = True
                self.X_reward+=-10
                self.D_reward+=10
                return self.end_flag
        return self.end_flag

# Takes action . Target and mode are lists. planning is "random" for now. Mode = mode of transport, type detective /X
    # example mode : [4,1] , target [46] means that you take a hidden move and use taxi to go to 46
    def take_action(self,target,type,mode,index,planning = "None"):
        action_det_reward,action_x_reward = 0,0
        if(type == "detective"):
            agent = self.detectives[index]

            print("Detective ",index," Cards left : ", agent.cards)

            if(planning == "random"):
                (target,mode_new) = self.random_action(type,mode,agent)
                # If there is no viable target, action fails.
                if(target == -1):
                    print("Detective ", index, "Failed ... \n")
                    return (-1,-1,0,self.end_flag)

                print("Target,Mode : ",target,mode_new)
                agent.take_action(target, mode_new)
            else:
                print("Target,Mode : " , target,mode)
                agent.take_action(target,mode)
                mode_new = mode
            # Update the observation
            self.observation.update_observation(type,index,agent)
            action_det_reward = self.reward('Detective')
            self.D_reward+=action_det_reward
            #self.print_reward()

        else:
            print("X Cards left : ", self.X.cards)
            if(planning == "random"):
                (target,mode_new) = self.random_action(type,mode,self.X)
                # No viable actions
                if(target == -1):
                    # Failed moved still counted as move here
                    self.X.moves+=1

                    if(len(mode) > 0 and mode[0]==3):
                        self.X.moves+=1

                    self.move = self.X.moves

                    print("X Failed ..")
                    return (-1,0,-1,self.end_flag)

                print("Target/Mode : ", target,mode_new)
                self.X.take_action(target, mode_new)
            else:
                print("Target,Mode : ", target,mode)
                mode_new = mode
                self.X.take_action(target,mode)
            self.observation.update_observation(type,index,self.X)


            temp=set()
            for i in self.M:
                z=self.board.connections(i)
                if mode_new[0]==0:
                    for j in z[0]:
                        temp.add(j)
                if mode_new[0]==1:
                    for j in z[1]:
                        temp.add(j)
                if mode_new[0]==2:
                    for j in z[2]:
                        temp.add(j)
                if mode_new[0]==3:
                    for j in z[mode_new[1]]:
                        temp.add(j)
                    temp1=set()
                    for e in temp:
                        z2=self.board.connections(e)
                        for j in z2[mode_new[2]]:
                            temp1.add(j)
                    temp=temp1
                if mode_new[0]==4:
                    l=[0,1,2]
                    for k in l:
                        for j in z[k]:
                            temp.add(j)
            for i in self.detectives:
                if i.position in temp:
                    temp.remove(i.position)
            self.M=temp

            #self.print_reward()

        reward = 0

        self.move = self.X.moves
        if self.move in [3,8,13,18]:
            self.M={self.X.position}

        action_x_reward = self.reward('X')
        self.X_reward+=action_x_reward
        self.finish()
        if(not self.end_flag):
            for i in self.detectives:
                if i.position in self.M:
                    self.M.remove(i.position)

        return (self.observation,action_det_reward,action_x_reward,self.end_flag)

    def random_action(self,type,mode,agent):
        if(type == "detective"):
            (target,action) = self.choose_random_target(agent)

            if(target < 0):
                return [-1,-1]

            return ([target],[action])

        else:
            if(not mode==[] and mode[0] == 3):
                (target1,action1) = self.choose_random_target(agent,type)
                if(target1 == -1):
                    return [-1,-1]
                (target2,action2) = self.choose_random_target(agent,type)
                if(target2 == -1):
                    return [-1,-1]
                return ([target1,target2],[3,action1,action2])

            else:
                (target1,action1) = self.choose_random_target(agent,type)
                if(target1 == -1):
                    return [-1,-1]
                if(not mode == [] and mode == 4):
                    return ([target1],[4,action1])
                else:
                    return ([target1],[action1])

    def isEmpty(self,node):
        for i in range(0,self.no_of_players):
            if(self.detectives[i].position == node):
                return False

        return True

    def choose_random_target(self,agent,type = "detective"):
        for i in range(0,10):
            # Try actions multiple times
            action = agent.random_action()

            if (action < 0):
                print("No actions left ")
                return (-2, -1)

            l = self.board.connections(agent.position)[action]

            #print(action,self.board.connections(agent.position))

            if(l == []):
                # We retry with a new action
                continue

            if(type == "x"):
                for i in range(0,10):
                    target = random.sample(l, 1)[0]
                    if(self.isEmpty(target)):
                        return (target,action)

            else:
                target = random.sample(l,1)[0]
                return (target,action)
        if(type=="x"):
            self.end_flag=True
            self.X_reward-=10
            self.D_reward+=10
        else:
            self.D_reward-=1
        print("No empty spot")
        return (-1,-1)

    def print_pos(self):
        positions = [x.position for x in self.detectives]
        positions.append(self.X.position)
        print("Positions of Detective and X " ,positions)
        return

    def reward(self,t):
        if t=='Detective':
            m=self.M
            d=self.detectives
            l=[]
            for i in d:
                min=200
                for k in m:
                    c=self.board.shortest_path(i.position,k)
                    if min>c:
                        min=c
                l.append(1/(4*(min+1)))
            #print(l)
            return sum(l)
        if t=='X':
            X=self.X.position
            d=self.detectives
            min=200
            c = 0
            for k in d:
                c=self.board.shortest_path(X,k.position)
                if min>c:
                    min=c
            return min/15
        return 0

    def print_reward(self):
        print("Reward collected by X is ", self.X_reward)
        print("Reward collected by Detective is ",self.D_reward)
    def return_reward(self):
        return (self.X_reward,self.D_reward)
    def list_of_action_x(self):
        return self.X.list_actions(self.board,self.detectives)

    # TODO: (Shaurya) Updates the feature vector
    def update(self):
        # self.f_d[for x in M - 1] = 1.0/len(M)
        return 0
