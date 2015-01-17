from math import *
import sys
import copy
from model.ActionType import ActionType
from model.World import World
from model.HockeyistState import HockeyistState
from model.Player import Player
from model.HockeyistType import HockeyistType

class MyStrategy:
    #***GENERAL PARAMETERS***
    k_abr = 0.02
    k_abr_puck = 0.001
    STRIKE_ANGLE = 1.0*pi/180.0
    border_angle = pi/2.0
    prediction_coords_velocity = 3.0
    puck_max_speed = 12.5
    #forward
    strike_pos_x = 535  
    strike_pos_y = -75
    strike_target_x = 535
    strike_target_y = -75
    pass_back = 335
    attack_hor_line = 130
    offset_x = 415
    offset_y = 300
    circle_strike = 110.0
    #defender
    net_pos_x_mid = -420.0
    net_pos_y_mid = 0
    def_area = 130.0

    def __init__(self):
        self.state = self.seeker

    def move(self, me, world, game, move):
        self.state(world, game, me, move)

    #Finite machine states

    def seeker(self, world, game, me, move):
        own_player = world.get_my_player()
        opp_player = world.get_opponent_player()
        puck = world.puck
        puck_x, puck_y = self.ct(world, game, puck.x, puck.y)
        nearest_own = self.nearest_own_to_point(world, game, puck_x, puck_y)       
        nearest_own_to_point_not_puck_owner = self.nearest_own_to_point_not_puck_owner(world, game, MyStrategy.net_pos_x_mid, MyStrategy.net_pos_y_mid)
        nearest_own_to_point_not_seeker = self.nearest_own_to_point_not_seeker(world, game, MyStrategy.net_pos_x_mid, MyStrategy.net_pos_y_mid)
        nearest_own_to_point_not_selected_seeker, seeker_index, min_ticks = self.nearest_own_to_point_not_selected_seeker(world, game, MyStrategy.net_pos_x_mid, MyStrategy.net_pos_y_mid)
        if me.state != 3:
            if self.subs(world, game, me) == True:
                x = -0.5*((game.rink_left + game.rink_right)/2.0 - game.rink_left)
                y = (game.rink_top + game.rink_bottom)/2.0 - game.rink_top - game.substitution_area_height/2.0
                move.speed_up, move.turn, S_act, state = self.get_point_for(world, game, me, x, y)
                move.teammate_index = self.subs_index(world, game, me)
                move.action = ActionType.SUBSTITUTE
            else:
                if puck.owner_player_id == own_player.id:
                    if puck.owner_hockeyist_id == me.id:
                        self.state = self.attack
                    else:
                        if nearest_own_to_point_not_puck_owner == me.teammate_index:
                            self.state = self.defense
                        else:
                            self.state = self.midfielder
                elif puck.owner_player_id == opp_player.id:
                    if seeker_index == me.teammate_index:
                        move.speed_up, move.turn, move.action = self.seeker_target_puck(world, game, me)
                    else:
                        if nearest_own_to_point_not_selected_seeker == me.teammate_index:
                            self.state = self.defense
                        else:
                            self.state = self.midfielder
                else:
                    if seeker_index == me.teammate_index:
                        move.speed_up, move.turn, move.action = self.seeker_target_puck(world, game, me)                        
                    else:  
                        if nearest_own_to_point_not_selected_seeker == me.teammate_index: 
                            self.state = self.defense
                        else:
                            self.state = self.midfielder                

    def attack(self, world, game, me, move):
        puck = world.puck
        own_player = world.get_my_player()
        opp_player = world.get_opponent_player()
        puck_x, puck_y = self.ct(world, game, puck.x, puck.y)
        nearest_own = self.nearest_own_to_point(world, game, puck_x, puck_y)
        nearest_own_to_point_not_puck_owner = self.nearest_own_to_point_not_puck_owner(world, game, MyStrategy.net_pos_x_mid, MyStrategy.net_pos_y_mid)
        nearest_own_to_point_not_seeker = self.nearest_own_to_point_not_seeker(world, game, MyStrategy.net_pos_x_mid, MyStrategy.net_pos_y_mid)
        nearest_own_to_point_not_selected_seeker, seeker_index, min_ticks = self.nearest_own_to_point_not_selected_seeker(world, game, MyStrategy.net_pos_x_mid, MyStrategy.net_pos_y_mid)
        if me.state != 3:
            if self.subs(world, game, me) == True:
                x = -0.5*((game.rink_left + game.rink_right)/2.0 - game.rink_left)
                y = (game.rink_top + game.rink_bottom)/2.0 - game.rink_top - game.substitution_area_height/2.0
                move.speed_up, move.turn, S_act, state = self.get_point_for(world, game, me, x, y)
                move.teammate_index = self.subs_index(world, game, me)
                move.action = ActionType.SUBSTITUTE
            else:
                if puck.owner_player_id == own_player.id:
                    if puck.owner_hockeyist_id == me.id:
                        move.speed_up, move.turn, move.action, move.pass_angle, move.pass_power = self.attack_target_strike_spot(world, game, me)
                    else:
                        if nearest_own_to_point_not_puck_owner == me.teammate_index:
                            self.state = self.defense
                        else:
                            self.state = self.midfielder
                elif puck.owner_player_id == opp_player.id:
                    if seeker_index == me.teammate_index:
                        self.state = self.seeker                        
                    else:
                        if nearest_own_to_point_not_selected_seeker == me.teammate_index:
                            self.state = self.defense
                        else:
                            self.state = self.midfielder
                else:
                    if seeker_index == me.teammate_index:
                        self.state = self.seeker
                    else:
                        if nearest_own_to_point_not_selected_seeker == me.teammate_index:
                            self.state = self.defense
                        else:
                            self.state = self.midfielder

    def defense(self, world, game, me, move):
        puck = world.puck
        own_player = world.get_my_player()
        opp_player = world.get_opponent_player()
        puck_x, puck_y = self.ct(world, game, puck.x, puck.y)
        nearest_own = self.nearest_own_to_point(world, game, puck_x, puck_y)
        nearest_own_to_point_not_puck_owner = self.nearest_own_to_point_not_puck_owner(world, game, MyStrategy.net_pos_x_mid, MyStrategy.net_pos_y_mid)
        nearest_own_to_point_not_seeker = self.nearest_own_to_point_not_seeker(world, game, MyStrategy.net_pos_x_mid, MyStrategy.net_pos_y_mid)
        nearest_own_to_point_not_selected_seeker, seeker_index, min_ticks = self.nearest_own_to_point_not_selected_seeker(world, game, MyStrategy.net_pos_x_mid, MyStrategy.net_pos_y_mid)
        if me.state != 3:
            if self.subs(world, game, me) == True:
                x = -0.5*((game.rink_left + game.rink_right)/2.0 - game.rink_left)
                y = (game.rink_top + game.rink_bottom)/2.0 - game.rink_top - game.substitution_area_height/2.0
                move.speed_up, move.turn, S_act, state = self.get_point_for(world, game, me, x, y)
                move.teammate_index = self.subs_index(world, game, me)
                move.action = ActionType.SUBSTITUTE
            else:
                if puck.owner_player_id == own_player.id:
                    if puck.owner_hockeyist_id == me.id:
                        self.state = self.attack
                    else:
                        if nearest_own_to_point_not_puck_owner == me.teammate_index:
                            direct = self.defense_direct_select(world, game, me)  
                            if direct == "forward":
                                move.speed_up, move.turn, S_act, state = self.get_point_for(world, game, me, MyStrategy.net_pos_x_mid, MyStrategy.net_pos_y_mid)
                            else:
                                move.speed_up, move.turn, S_act, state = self.get_point_rev(world, game, me, MyStrategy.net_pos_x_mid, MyStrategy.net_pos_y_mid)
                            move.action = self.check_action_puck(world, game, me)
                            self.state = self.defense
                        else:
                            self.state = self.midfielder
                elif puck.owner_player_id == opp_player.id:
                    if seeker_index == me.teammate_index:
                        self.state = self.seeker
                    else:
                        if nearest_own_to_point_not_selected_seeker == me.teammate_index:
                            direct = self.defense_direct_select(world, game, me)  
                            if direct == "forward":
                                move.speed_up, move.turn, S_act, state = self.get_point_for(world, game, me, MyStrategy.net_pos_x_mid, MyStrategy.net_pos_y_mid)
                            else:
                                move.speed_up, move.turn, S_act, state = self.get_point_rev(world, game, me, MyStrategy.net_pos_x_mid, MyStrategy.net_pos_y_mid)
                            move.action = self.check_action_puck(world, game, me)
                            self.state = self.defense
                        else:
                            self.state = self.midfielder
                else:
                    if seeker_index == me.teammate_index:
                        self.state = self.seeker
                    else:
                        if nearest_own_to_point_not_selected_seeker == me.teammate_index:
                            direct = self.defense_direct_select(world, game, me)  
                            if direct == "forward":
                                move.speed_up, move.turn, S_act, state = self.get_point_for(world, game, me, MyStrategy.net_pos_x_mid, MyStrategy.net_pos_y_mid)
                            else:
                                move.speed_up, move.turn, S_act, state = self.get_point_rev(world, game, me, MyStrategy.net_pos_x_mid, MyStrategy.net_pos_y_mid)
                            move.action = self.check_action_puck(world, game, me)
                            self.state = self.defense
                        else:
                            self.state = self.midfielder

    def midfielder(self, world, game, me, move):
        puck = world.puck
        own_player = world.get_my_player()
        opp_player = world.get_opponent_player()
        puck_x, puck_y = self.ct(world, game, puck.x, puck.y)
        nearest_own = self.nearest_own_to_point(world, game, puck_x, puck_y)
        nearest_own_to_point_not_puck_owner = self.nearest_own_to_point_not_puck_owner(world, game, MyStrategy.net_pos_x_mid, MyStrategy.net_pos_y_mid)
        nearest_own_to_point_not_seeker = self.nearest_own_to_point_not_seeker(world, game, MyStrategy.net_pos_x_mid, MyStrategy.net_pos_y_mid)
        nearest_own_to_point_not_selected_seeker, seeker_index, min_ticks = self.nearest_own_to_point_not_selected_seeker(world, game, MyStrategy.net_pos_x_mid, MyStrategy.net_pos_y_mid)
        if me.state != 3:
            if self.subs(world, game, me) == True:
                x = -0.5*((game.rink_left + game.rink_right)/2.0 - game.rink_left)
                y = (game.rink_top + game.rink_bottom)/2.0 - game.rink_top - game.substitution_area_height/2.0
                move.speed_up, move.turn, S_act, state = self.get_point_for(world, game, me, x, y)
                move.teammate_index = self.subs_index(world, game, me)
                move.action = ActionType.SUBSTITUTE
            else:
                if puck.owner_player_id == own_player.id:
                    if puck.owner_hockeyist_id == me.id:
                        self.state = self.attack
                    else:
                        if nearest_own_to_point_not_puck_owner == me.teammate_index:
                            self.state = self.defense
                        else:
                            move.speed_up, move.turn, move.action = self.midfielder_go_for_pass(world, game, me)
                elif puck.owner_player_id == opp_player.id:
                    if seeker_index == me.teammate_index:
                        self.state = self.seeker
                    else:
                        if nearest_own_to_point_not_selected_seeker == me.teammate_index:
                            self.state = self.defense
                        else:
                            move.speed_up, move.turn, move.action = self.midfielder_close_opp(world, game, me)
                else:
                    if seeker_index == me.teammate_index:
                        self.state = self.seeker
                    else:
                        if nearest_own_to_point_not_selected_seeker == me.teammate_index:
                            self.state = self.defense
                        else:
                            move.speed_up, move.turn, move.action = self.midfielder_go_for_pass(world, game, me)




#================================================SPECIFIC METHODS======================================================

#************************************************SEEKER****************************************************

    def emul_move_rev(self, world, game, hockeyist_original, x_target, y_target):
        hockeyist = copy.copy(hockeyist_original)
        k_f = game.hockeyist_speed_up_factor * (hockeyist.agility*0.75 + hockeyist.agility*0.25*hockeyist.stamina/2000.0) / 100
        k_b = game.hockeyist_speed_down_factor * (hockeyist.agility*0.75 + hockeyist.agility*0.25*hockeyist.stamina/2000.0) / 100
        turn_angle = pi/60.0*(hockeyist.agility*0.75 + hockeyist.agility*0.25*hockeyist.stamina/2000.0) / 100
        i = 0
        while i < 50: 
            speed_up, turn, S_act, state = self.get_point_rev(world, game, hockeyist,  x_target, y_target)
            if speed_up > 0:
                accel = speed_up * k_f
            else:
                accel = speed_up * k_b
            if abs(turn) > turn_angle:
                hockeyist.angle += turn_angle*copysign(1.0, turn)
            else:
                hockeyist.angle += turn
            hockeyist.speed_x += - hockeyist.speed_x * MyStrategy.k_abr + accel * cos(hockeyist.angle)
            hockeyist.speed_y += - hockeyist.speed_y * MyStrategy.k_abr + accel * sin(hockeyist.angle)
            hockeyist.x += hockeyist.speed_x
            hockeyist.y += hockeyist.speed_y
            i += 1
            if state == True:
                return i
        return -1

    def defense_direct_select(self, world, game, me):
        puck = world.puck
        c = 0
        own_player = world.get_my_player()
        opp_player = world.get_opponent_player()
        net_own_x, net_own_y = self.ct_inv(world, game, MyStrategy.net_pos_x_mid, MyStrategy.net_pos_y_mid)
        angle = me.get_angle_to(net_own_x, net_own_y)
        x, y = self.ct(world, game, net_own_x, net_own_y)
        nearest_opp = self.nearest_opp_to_point(world, game, x, y)
        opp_x, opp_y, opp_speed_x, opp_speed_y = self.opp_index(world, game, nearest_opp)
        me_x, me_y = self.ct(world, game, me.x, me.y)
        if hypot(me_x - x, me_y - y) < hypot(opp_x - x, opp_y - y)/2.0 and abs(angle) > MyStrategy.border_angle:
            return "backward"
        else:
            return "forward"

    def seeker_target_puck(self, world, game, me):
        opp_player = world.get_opponent_player()
        own_player = world.get_my_player()
        puck = world.puck
        nearest_own_to_point = self.nearest_own_to_point(world, game, MyStrategy.net_pos_x_mid, MyStrategy.net_pos_y_mid)    
        puck_x, puck_y = self.ct(world, game, puck.x, puck.y)
        me_x, me_y = self.ct(world, game, me.x, me.y)
        if me.teammate_index == nearest_own_to_point and puck.owner_player_id != own_player.id:
            x, y = puck.x, puck.y
        else:
            x, y = self.predict_coords_accel(world, game, me, puck.x, puck.y, puck.speed_x, puck.speed_y)            
        action = self.check_action_puck(world, game, me)
        x_target, y_target = self.ct(world, game, x, y)
        speed_up, turn, S_act, state = self.get_point_for_wb(world, game, me, x_target, y_target)
        if hypot(me_x - puck_x, me_y - puck_y) < game.stick_length/2.0 and abs(me.get_angle_to(puck.x, puck.y)) < game.stick_sector/2.0 and puck.owner_player_id == opp_player.id:
            speed_up = -1.0
        puck_predict, index = self.check_puck_fly_strike( world, game, me)
        strike_pos = self.attack_pos_shape(me_x, me_y)
        action = self.check_action_puck(world, game, me)
        if puck_predict == True and strike_pos != 0:
            strike_pos_x = MyStrategy.strike_target_x
            strike_pos_y = MyStrategy.strike_target_y * copysign(1.0, me_y)
            x, y = self.ct_inv(world, game, strike_pos_x, strike_pos_y)
            turn = me.get_angle_to(x, y)
            speed_up = 0.0
        if puck_predict == True and strike_pos == 0 and action == ActionType.STRIKE:
            nearest_own_to_point_not_def = self.nearest_own_to_point_not_def(world, game, me_x, me_y)
            own_x, own_y, own_speed_x, own_speed_y = self.own_index(world, game, nearest_own_to_point_not_def)
            x, y = self.ct_inv(world, game, own_x, own_y)
            turn = me.get_angle_to(x, y)
            speed_up = 0.0
            if abs(me.get_angle_to(puck.x, puck.y)) > game.stick_sector / 2.2:
                turn = me.get_angle_to(puck.x, puck.y)
        return speed_up, turn, action

    def check_action_puck(self, world, game, me):
        puck = world.puck
        action = ActionType.TAKE_PUCK
        opp_player = world.get_opponent_player()
        own_player = world.get_my_player()
        puck_x, puck_y = self.ct(world, game, puck.x, puck.y)
        me_x, me_y = self.ct(world, game, me.x, me.y)
        nearest_opp = self.nearest_opp_to_point(world, game, me_x, me_y)
        opp_x, opp_y, opp_speed_x, opp_speed_y = self.opp_index(world, game, nearest_opp)
        x, y = self.ct_inv(world, game, opp_x, opp_y)
        puck_cur_dist = hypot(puck.x - me.x, puck.y - me.y)
        puck_cur_speed = hypot(puck.speed_x,puck.speed_y)
        opp_cur_dist = hypot(x - me.x, y - me.y)
        strike_target_state = self.check_pos_strike(world, game, me)
        puck_predict, index = self.check_puck_fly_strike(world, game, me)
        if puck_cur_dist < game.stick_length and abs(me.get_angle_to(puck.x, puck.y)) < game.stick_sector/2.0 and puck.owner_player_id == -1:
            if strike_target_state == True:
                action = ActionType.STRIKE
            elif me.swing_ticks > 0:
                action = ActionType.STRIKE
            else:
                if puck_cur_speed >= MyStrategy.puck_max_speed:
                    action = ActionType.STRIKE
                else:
                    action = ActionType.TAKE_PUCK
        elif puck_cur_dist < game.stick_length and abs(me.get_angle_to(puck.x, puck.y)) < game.stick_sector/2.0 and puck.owner_player_id == opp_player.id:
            action = ActionType.STRIKE
        else:
            action = ActionType.TAKE_PUCK
            if puck_predict == True and strike_target_state == True and index <= 20:
                action = ActionType.SWING
            elif opp_cur_dist < game.stick_length and abs(me.get_angle_to(x, y)) < game.stick_sector/2.0 and puck_predict == False:
                action = ActionType.STRIKE
        #check to prevent swing freezes
        if me.swing_ticks > 0 and puck_predict == False:
            action = ActionType.STRIKE 
        #check to prevent auto goals
        x1, y1 = self.ct_inv(world, game, -MyStrategy.strike_target_x, MyStrategy.strike_target_y)
        x2, y2 = self.ct_inv(world, game, -MyStrategy.strike_target_x, -MyStrategy.strike_target_y)
        if me.get_angle_to(x1, y1) - 4*MyStrategy.STRIKE_ANGLE < 0 and me.get_angle_to(x2, y2) + 4*MyStrategy.STRIKE_ANGLE > 0:
            action = ActionType.TAKE_PUCK
        #to take puck, not strike, when puck is not going to the net
        if puck.owner_player_id == -1 and me.swing_ticks == 0:
            x, y = self.ct_inv(world, game, MyStrategy.strike_target_x, MyStrategy.strike_target_y)
            puck_speed_x, puck_speed_y = self.ct_speed(world, game, puck.speed_x, puck.speed_y)
            tg_alpha_puck = -puck.speed_y/(puck.speed_x + 0.001)
            y_strike = puck_y - copysign(1.0, x - 600)*(puck_x - (-MyStrategy.strike_target_x))*tg_alpha_puck
            if abs(abs(y_strike) - 75) > 35 or abs(puck.speed_y) < game.goalie_max_speed:
                action = ActionType.TAKE_PUCK
        if puck_cur_dist < game.stick_length and abs(me.get_angle_to(puck.x, puck.y)) < game.stick_sector/2.0 and puck.owner_player_id == own_player.id and puck.owner_hockeyist_id != me.id:
            action = ActionType.NONE
        return action

    def check_swing(self, me):
        if me.swing_ticks > 0:
            action = ActionType.STRIKE
        else:
            action = ActionType.TAKE_PUCK
        return action 

    def check_puck_fly_strike(self, world, game, me):
        #check on X ticks forward will puck be near me or not (for strike)
        puck = world.puck
        opp_player = world.get_opponent_player()
        i = 0
        if puck.owner_player_id == opp_player.id:
            return False, -1
        while i < 150: 
            time = float(i)
            x = puck.x + puck.speed_x/MyStrategy.k_abr_puck * (1 - exp(-MyStrategy.k_abr_puck*time))
            y = puck.y + puck.speed_y/MyStrategy.k_abr_puck * (1 - exp(-MyStrategy.k_abr_puck*time))
            me_x_pr, me_y_pr = self.predict_coords_free_hock(world, game, time, me.x, me.y, me.speed_x, me.speed_y) 
            i += 1
            if hypot(x - me_x_pr, y - me_y_pr) < game.stick_length and abs(me.get_angle_to(x, y)) < game.stick_sector/2.0:
                return True, i
        return False, -1

    def predict_coords_accel(self, world, game, me, x, y, speed_x, speed_y):
        #approximate prediction of future postition of free unit when pursuing by accelerating unit
        #not universal coordinates are used
        T = hypot(x - me.x, y - me.y) / min((game.hockeyist_max_speed,(hypot(me.speed_x, me.speed_y) + MyStrategy.prediction_coords_velocity)))
        if  hypot(x - me.x, y - me.y) < game.stick_length:
            T = 0.0
        x = x + speed_x * T
        y = y + speed_y * T
        return x, y

    def predict_coords_free_hock(self, world, game, time, x, y, speed_x, speed_y):
        #prediction of cooords of free agent after time 
        #not universal coordinates are used     
        x = x + speed_x/MyStrategy.k_abr * (1 - exp(-MyStrategy.k_abr*time))
        y = y + speed_y/MyStrategy.k_abr * (1 - exp(-MyStrategy.k_abr*time))
        return x, y

    def predict_coords_free_puck(self, world, game, time, x, y, speed_x, speed_y):
        #prediction of cooords of free agent after time 
        #not universal coordinates are used     
        x = x + speed_x/MyStrategy.k_abr_puck * (1 - exp(-MyStrategy.k_abr_puck*time))
        y = y + speed_y/MyStrategy.k_abr_puck * (1 - exp(-MyStrategy.k_abr_puck*time))
        return x, y

    def predict_time_free_puck(self, world, game, dist, v0):
        #prediction of time needed for free agent to pass distance dist
        #not universal coordinates are used     
        #ONLY FOR PUCK!!
        if v0 == 0.0:
            return -1
        if MyStrategy.k_abr_puck*dist/v0 > 1:
            return -1
        else:
            time = -(1.0/MyStrategy.k_abr_puck)*log(1-MyStrategy.k_abr_puck*dist/v0)
            return time
                 
    def check_pos_strike(self, world, game, me):
        me_x, me_y = self.ct(world, game, me.x, me.y)
        strike_pos_state = self.attack_pos_shape(me_x, me_y)
        strike_pos_x = MyStrategy.strike_target_x
        strike_pos_y = MyStrategy.strike_target_y * copysign(1.0, me_y)
        x, y = self.ct_inv(world, game, strike_pos_x, strike_pos_y)
        turn = me.get_angle_to(x, y)
        if abs(turn) < MyStrategy.STRIKE_ANGLE:
            strike_angle_state = True
        else:
            strike_angle_state = False
        if strike_pos_state != 0 and strike_angle_state == True:
            return True
        else:
            return False

#************************************************ATTACK****************************************************

    def attack_pos_shape(self, x, y):
        if -MyStrategy.pass_back/2.0 <= x <= 0 and abs(y) >= MyStrategy.attack_hor_line:
            return 1
        elif 0 < x <= MyStrategy.pass_back and abs(y) >= MyStrategy.attack_hor_line:
            return 2
        else:
            return 0

    def attack_target_pass_back(self, me, world, game): 
        nearest_to_net_own = self.nearest_own_to_point(world, game, MyStrategy.net_pos_x_mid , MyStrategy.net_pos_y_mid )
        x, y, speed_x, speed_y = self.own_index(world, game, nearest_to_net_own)
        x, y = self.ct_inv(world, game, x, y)
        x, y = self.predict_coords(game, me, x, y, speed_x, -speed_y)
        angle = me.get_angle_to(x, y)
        #number 2.1 used not 2.0 to avoid fluctuations
        if abs(angle) < game.pass_sector / 2.1:
            action = ActionType.PASS
            speed_up = 0.0
            turn = angle
            return speed_up, turn, action, angle
        else:
            action = ActionType.TAKE_PUCK
            speed_up = 0.0
            turn = angle
            return speed_up, turn, action, angle

    def attack_check_strike_pos(self, world, game, me):
        state = False
        opp_player = world.get_opponent_player()
        puck = world.puck  
        puck_x, puck_y = self.ct(world, game, puck.x, puck.y)   
        me_x, me_y = self.ct(world, game, me.x, me.y)
        nearest_opp = self.nearest_opp_to_point(world, game, puck_x, puck_y)
        opp_x, opp_y, opp_speed_x, opp_speed_y = self.opp_index(world, game, nearest_opp)
        action = ActionType.TAKE_PUCK
        if me.swing_ticks == 0:
            y_shift = self.strike_target_shift(world, game, me)
        else:
            y_shift = 0.0
        if me.swing_ticks > 0:
            action = ActionType.SWING
        strike_target_x = MyStrategy.strike_target_x
        strike_target_y = MyStrategy.strike_target_y * copysign(1.0, me_y) + y_shift
        x, y = self.ct_inv(world, game, strike_target_x, strike_target_y)
        angle = me.get_angle_to(x, y)                     
        if self.attack_pos_shape(me_x, me_y) != 0 and abs(angle) < MyStrategy.STRIKE_ANGLE:
            state = True
            action = ActionType.SWING
        if self.attack_pos_shape(me_x, me_y) != 0 and abs(angle) < MyStrategy.STRIKE_ANGLE and me.swing_ticks > 1: # and hypot(puck_x - opp_x, puck_y - opp_y) > game.stick_length:
            state = True
            action = ActionType.STRIKE
        if me.swing_ticks >= 20:
            state = True
            action = ActionType.STRIKE
        if me.swing_ticks >= 20:
            state = True
            action = ActionType.STRIKE
        return action, state

    def attack_target_strike_spot(self, world, game, me): 
        pass_angle = 0.0
        pass_power = 0.6
        puck = world.puck
        puck_x, puck_y = self.ct(world, game, puck.x, puck.y)
        me_x, me_y = self.ct(world, game, me.x, me.y)
        nearest_opp = self.nearest_opp_to_point(world, game, puck_x, puck_y)
        nearest_own_not_me = self.nearest_own_to_point_not_me(world, game, me, puck_x, 0)
        nearest_own_not_me_mid = self.nearest_own_to_point_not_me(world, game, me, (game.rink_right - game.rink_left)/2.0, 0)
        own_player = world.get_my_player()
        opp_player = world.get_opponent_player()
        opp_x, opp_y, opp_speed_x, opp_speed_y = self.opp_index(world, game, nearest_opp)
        own_x_mid, own_y_mid, own_speed_x_mid, own_speed_y_mid = self.own_index(world, game, nearest_own_not_me_mid)
        sign, offset_x, offset_y = self.sign_and_offset(world, game, me)
        strike_pos_x = MyStrategy.strike_pos_x + offset_x
        strike_pos_y = MyStrategy.strike_pos_y * sign + offset_y  
        if self.select_hock_for_pass(world, game, me) != False: 
            own_mid_obj = self.select_hock_for_pass(world, game, me)
            pass_direct_x = cos(own_mid_obj.angle)*game.stick_length*2.0/3.0
            pass_direct_y = sin(own_mid_obj.angle)*game.stick_length*2.0/3.0
            own_x_mid, own_y_mid = self.ct(world, game, pass_direct_x + own_mid_obj.x, pass_direct_y + own_mid_obj.y)
            own_speed_x_mid, own_speed_y_mid = self.ct_speed(world, game, own_mid_obj.speed_x, own_mid_obj.speed_y)
        if me.swing_ticks == 0:
            y_shift = self.strike_target_shift(world, game, me)
        else:
            y_shift = 0.0
        strike_target_x = MyStrategy.strike_target_x
        strike_target_y = MyStrategy.strike_target_y * sign + y_shift             
        x, y = self.ct_inv(world, game, strike_pos_x, strike_pos_y)
        dist = hypot(me.x - x, me.y - y)
        action, state = self.attack_check_strike_pos(world, game, me)
        if me_x > MyStrategy.pass_back:
            speed_up, angle, action, pass_angle = self.attack_target_pass_back(me, world, game)  
            pass_power = 0.8                 
            if self.attack_pos_shape(own_x_mid, own_y_mid) != 0 and self.select_hock_for_pass(world, game, me) != False:
                pass_power = 0.6
                #to make pass on the spot before the teammate, not at him
                x, y = self.ct_inv(world, game, own_x_mid, own_y_mid)
                speed_x, speed_y = self.ct_inv_speed(world, game, own_speed_x_mid, own_speed_y_mid)
                angle_to_pass_obj = me.get_angle_to(x, y)
                angle_to_velocity = me.get_angle_to(me.speed_x + me.x, me.speed_y + me.y)
                v0 = pass_power*15+hypot(me.speed_x, me.speed_y)*cos(angle_to_pass_obj - angle_to_velocity)
                dist_to_own = hypot(puck_x - own_x_mid, puck_y - own_y_mid)
                time = self.predict_time_free_puck(world, game, dist_to_own, v0)
                x, y = self.predict_coords_free_hock(world, game, time, x, y, speed_x, speed_y)
                speed_up = 1.0
                angle = me.get_angle_to(x, y)
                action = ActionType.TAKE_PUCK
                if abs(angle) < game.pass_sector/2.1:
                    pass_angle = angle
                    action = ActionType.PASS            
        elif me_x < 0:
            x, y = self.get_force_x_y(world, game, me, sign, strike_pos_x, strike_pos_y)            
            speed_up, angle, S_act, state = self.get_point_for_wb(world, game, me, x,y)
            speed_up = 1.0
            action = ActionType.TAKE_PUCK
            dist_to_opp = hypot(opp_x - me_x, opp_y - me_y)
            if self.attack_pos_shape(me_x, me_y) == 0 and self.select_hock_for_pass(world, game, me) != False and (opp_x > puck_x or dist_to_opp < game.stick_length):
            #if self.attack_pos_shape(me_x, me_y) == 0:
                pass_power = 0.5
                #to make pass on the spot before the teammate, not at him
                x, y = self.ct_inv(world, game, own_x_mid, own_y_mid)
                speed_x, speed_y = self.ct_inv_speed(world, game, own_speed_x_mid, own_speed_y_mid)
                angle_to_pass_obj = me.get_angle_to(x, y)
                angle_to_velocity = me.get_angle_to(me.speed_x + me.x, me.speed_y + me.y)
                v0 = pass_power*15+hypot(me.speed_x, me.speed_y)*cos(angle_to_pass_obj - angle_to_velocity)
                dist_to_own = hypot(puck_x - own_x_mid, puck_y - own_y_mid)
                time = self.predict_time_free_puck(world, game, dist_to_own, v0)
                x, y = self.predict_coords_free_hock(world, game, time, x, y, speed_x, speed_y)
                speed_up = 1.0
                angle = me.get_angle_to(x, y)
                action = ActionType.TAKE_PUCK
                if abs(angle) < game.pass_sector/2.1:
                    pass_angle = angle
                    action = ActionType.PASS
        elif MyStrategy.pass_back >= me_x >= 0.0:
            dist_to_own = hypot(puck_x - own_x_mid, puck_y - own_y_mid)
            dist_to_opp = hypot(opp_x - me_x, opp_y - me_y)
            # !!!!!!!!!!!!!!!!!! consider coeff 2.0 below
            if hypot(puck_x - opp_x, puck_y - opp_y) < 2.0*game.stick_length and self.attack_pos_shape(own_x_mid, own_y_mid) != 0 and me.swing_ticks == 0 and self.select_hock_for_pass(world, game, me) != False and (opp_x > puck_x or dist_to_opp < game.stick_length): 
                pass_power = 0.5
                x, y = self.ct_inv(world, game, own_x_mid, own_y_mid)
                speed_x, speed_y = self.ct_inv_speed(world, game, own_speed_x_mid, own_speed_y_mid)
                angle_to_pass_obj = me.get_angle_to(x, y)
                angle_to_velocity = me.get_angle_to(me.speed_x + me.x, me.speed_y + me.y)
                v0 = pass_power*15+hypot(me.speed_x, me.speed_y)*cos(angle_to_pass_obj - angle_to_velocity)
                time = self.predict_time_free_puck(world, game, dist_to_own, v0)
                x, y = self.predict_coords_free_hock(world, game, time, x, y, speed_x, speed_y)
                speed_up = 1.0
                angle = me.get_angle_to(x, y)
                action = ActionType.TAKE_PUCK
                if abs(angle) < game.pass_sector/2.1:
                    pass_angle = angle
                    action = ActionType.PASS
            else:
                if self.attack_pos_shape(me_x, me_y) != 0:
                    x, y = self.ct_inv(world, game, strike_target_x, strike_target_y)
                    angle = me.get_angle_to(x, y)
                    speed_up = 0.5
                else:
                    speed_up, angle, action, pass_angle = self.attack_target_pass_back(me, world, game)  
                    pass_power = 1.0 
        else:
            x, y = self.ct_inv(world, game, strike_target_x, strike_target_y)
            angle = me.get_angle_to(x, y)
            speed_up = 1.0
            action = ActionType.TAKE_PUCK
        if me.swing_ticks >= 20:
            state = True
            action = ActionType.STRIKE
        return speed_up, angle, action, pass_angle, pass_power

    def sign_and_offset(self, world, game, me):
        sign = 1.0
        offset_x = 0.0
        offset_y = 0.0
        puck = world.puck
        puck_x, puck_y = self.ct(world, game, puck.x, puck.y)
        me_x, me_y = self.ct(world, game, me.x, me.y)
        nearest_opp = self.nearest_opp_to_point(world, game, puck_x, puck_y)
        opp_player = world.get_opponent_player()
        opp_x_ct, opp_y_ct, opp_speed_x_ct, opp_speed_y_ct = self.opp_index(world, game, nearest_opp)
        opp_x, opp_y = self.ct_inv(world, game, opp_x_ct, opp_y_ct)
        x, wall_top = self.ct_inv(world, game, 0, game.rink_top)
        x, wall_bottom = self.ct_inv(world, game, 0, game.rink_bottom)
        if me_x >= 0:
            sign = copysign(1.0, me_y)
            offset_x = 0.0
            offset_y = 0.0
        elif me_x < 0 and me_x < opp_x_ct:
            if wall_top - opp_y_ct < wall_top - me_y:
                sign = -1.0
                offset_x = -MyStrategy.offset_x
                offset_y = MyStrategy.offset_y*sign
            else:
                sign = 1.0
                offset_x = -MyStrategy.offset_x
                offset_y = MyStrategy.offset_y*sign
        elif me_x < 0 and me_x > opp_x_ct:
            sign = copysign(1.0, me_y)
            offset_x = -MyStrategy.offset_x
            offset_y = MyStrategy.offset_y*sign
        return sign, offset_x, offset_y

    def strike_target_shift(self, world, game, me):
        puck = world.puck
        me_x, me_y = self.ct(world, game, me.x, me.y)
        me_speed_x, me_speed_y = self.ct_speed(world, game, me.speed_x, me.speed_y)
        puck_x, puck_y = self.ct(world, game, puck.x, puck.y)
        strike_target_x = MyStrategy.strike_target_x
        strike_target_y = MyStrategy.strike_target_y * copysign(1.0, me_y)            
        x, y = self.ct_inv(world, game, strike_target_x, strike_target_y)
        ticks = 20
        strike_target_x = MyStrategy.strike_target_x
        strike_target_y = MyStrategy.strike_target_y * copysign(1.0, me_y)    
        tang = abs(strike_target_y - me_y) / (strike_target_x - me_x)
        y_shift = me_speed_y*ticks*(-1.0) + tang*me_speed_x*ticks*copysign(1.0, me_y)*(-1.0)
        return y_shift 

    def check_pass(self, world, game, me, own_mid_obj):
        own_player = world.get_my_player()
        opp_player = world.get_opponent_player()
        me_x, me_y = self.ct(world, game, me.x, me.y)
        pass_direct_x = cos(own_mid_obj.angle)*game.stick_length*2.0/3.0
        pass_direct_y = sin(own_mid_obj.angle)*game.stick_length*2.0/3.0
        own_x_mid, own_y_mid = self.ct(world, game, pass_direct_x + own_mid_obj.x, pass_direct_y + own_mid_obj.y)
        #print world.tick, pass_direct_x, pass_direct_y
        x, y = self.ct_inv(world, game, own_x_mid, own_y_mid)
        close_count = 0
        for hockeyist in world.hockeyists:
            if hockeyist.player_id == opp_player.id and hockeyist.type != HockeyistType.GOALIE and hockeyist.state !=3:
                angle_opp = me.get_angle_to(hockeyist.x, hockeyist.y)
                angle_pass = me.get_angle_to(x, y)
                dist = hypot(me.x - hockeyist.x, me.y - hockeyist.y)
                if abs(sin(angle_opp - angle_pass))*dist < game.stick_length and abs(angle_opp - angle_pass) < pi/2.0 and dist > 65.0:
                    return False
        if hypot(own_x_mid - me_x, own_y_mid - me_y) < game.stick_length:
            return False
        return True

    def select_hock_for_pass(self, world, game, me):
        own_player = world.get_my_player()
        opp_player = world.get_opponent_player()
        for hockeyist in world.hockeyists:
            if hockeyist.player_id == own_player.id and hockeyist.type != HockeyistType.GOALIE and hockeyist.state !=3:
                if self.check_pass(world, game, me, hockeyist) == True:
                    return hockeyist
        return False




#************************************************MIDFIELDER****************************************************

    def midfielder_go_for_pass(self, world, game, me):
        puck = world.puck
        puck_x, puck_y = self.ct(world, game, puck.x, puck.y)
        me_x, me_y = self.ct(world, game, me.x, me.y)
        own_player = world.get_my_player()
        opp_player = world.get_opponent_player()
        sign = 1.0
        strike_pos_x = MyStrategy.strike_pos_x - MyStrategy.offset_x
        strike_pos_y = (MyStrategy.strike_pos_y + MyStrategy.offset_y) * (-1.0) * copysign(1.0, puck_y)
        strike_target_x = MyStrategy.strike_target_x
        strike_target_y = MyStrategy.strike_target_y * copysign(1.0, me_y)            
        x, y = self.ct_inv(world, game, strike_pos_x, strike_pos_y)
        dist = hypot(me.x - x, me.y - y)        
        puck_predict, index = self.check_puck_fly_strike( world, game, me)
        puck_cur_dist = hypot(puck.x - me.x, puck.y - me.y)
        if me_x < 0:
            x, y = self.get_force_x_y(world, game, me, sign, strike_pos_x, strike_pos_y)            
            speed_up, angle, S_act, state = self.get_point_for(world, game, me, x, y)
            speed_up = 1.0
            action = ActionType.TAKE_PUCK
        if me_x > 0:
            speed_up, angle, S_act, state = self.get_point_for(world, game, me, strike_pos_x, strike_pos_y)
            dist = hypot(me_x - strike_pos_x, me_y - strike_pos_y)
            action = ActionType.TAKE_PUCK
            if self.attack_pos_shape(me_x, me_y) != 0:
                x, y = self.ct_inv(world, game, strike_target_x, strike_target_y)
                angle = me.get_angle_to(x, y)
                speed_up = 0.0
                if puck_predict == True and index <= 20:
                    action = ActionType.SWING
        if me.swing_ticks > 0 and puck_predict == False:
            action = ActionType.STRIKE
        if puck_cur_dist < game.stick_length and abs(me.get_angle_to(puck.x, puck.y)) < game.stick_sector/2.0 and puck.owner_player_id == own_player.id and puck.owner_hockeyist_id != me.id:
            action = ActionType.NONE
        return speed_up, angle, action


    def midfielder_close_opp(self, world, game, me):
        action = ActionType.TAKE_PUCK
        rel_dist = 0.7
        puck = world.puck
        puck_x, puck_y = self.ct(world, game, puck.x, puck.y)
        me_x, me_y = self.ct(world, game, me.x, me.y)
        own_player = world.get_my_player()
        opp_player = world.get_opponent_player()            
        puck_predict, index = self.check_puck_fly_strike( world, game, me)
        nearest_opp_to_point_not_puck_owner = self.nearest_opp_to_point_not_puck_owner(world, game, MyStrategy.net_pos_x_mid, MyStrategy.net_pos_y_mid)
        opp_puck_owner = self.nearest_opp_to_point(world, game, puck_x, puck_y)
        opp_x, opp_y, opp_speed_x, opp_speed_y = self.opp_index(world, game, nearest_opp_to_point_not_puck_owner)
        opp_x_puck_owner, opp_y_puck_owner, opp_speed_x_puck_owner, opp_speed_y_puck_owner = self.opp_index(world, game, opp_puck_owner)
        puck_cur_dist = hypot(puck.x - me.x, puck.y - me.y)
        if opp_x_puck_owner < opp_x:
            x = opp_x_puck_owner
            y = opp_y_puck_owner
        else:
            if opp_x > 0:
                x = 0
                y = opp_y
            else:
                x = opp_x
                y = opp_y
        speed_up, angle, S_act, state = self.get_point_for(world, game, me, x, y)
        if hypot(me_x - x, me_y - y) < game.stick_length:
            x, y = self.ct_inv(world, game, x, y)
            angle = me.get_angle_to(x, y)
            if abs(angle) < game.stick_sector/2.0:
                action = ActionType.STRIKE
        else:
            if x > 0 and state == True:
                x, y = self.ct_inv(world, game, x, y)
                angle = me.get_angle_to(x, y)
        action = self.check_action_puck(world, game, me)
        if puck_cur_dist < game.stick_length and abs(me.get_angle_to(puck.x, puck.y)) < game.stick_sector/2.0 and puck.owner_player_id == own_player.id and puck.owner_hockeyist_id != me.id:
            action = ActionType.NONE
        return speed_up, angle, action
       
            
#************************************************DEFENSE****************************************************


    def defense_direct_select(self, world, game, me):
        puck = world.puck
        c = 0
        own_player = world.get_my_player()
        opp_player = world.get_opponent_player()
        net_own_x, net_own_y = self.ct_inv(world, game, MyStrategy.net_pos_x_mid, MyStrategy.net_pos_y_mid)
        angle = me.get_angle_to(net_own_x, net_own_y)
        x, y = self.ct(world, game, net_own_x, net_own_y)
        nearest_opp = self.nearest_opp_to_point(world, game, x, y)
        opp_x, opp_y, opp_speed_x, opp_speed_y = self.opp_index(world, game, nearest_opp)
        me_x, me_y = self.ct(world, game, me.x, me.y)
        if hypot(me_x - x, me_y - y) < hypot(opp_x - x, opp_y - y)/2.0 and abs(angle) > MyStrategy.border_angle:
            return "backward"
        else:
            return "forward"

#================================================GENERAL METHODS=======================================================

#coords transformation, search of players by indicies, etc

    def emul_move_for_wb(self, world, game, hockeyist_original, x_target, y_target):
        hockeyist = copy.copy(hockeyist_original)
        k_f = game.hockeyist_speed_up_factor * (hockeyist.agility*0.75 + hockeyist.agility*0.25*hockeyist.stamina/2000.0) / 100
        k_b = game.hockeyist_speed_down_factor * (hockeyist.agility*0.75 + hockeyist.agility*0.25*hockeyist.stamina/2000.0) / 100
        turn_angle = pi/60.0*(hockeyist.agility*0.75 + hockeyist.agility*0.25*hockeyist.stamina/2000.0) / 100
        i = 0
        while i < 200: 
            speed_up, turn, S_act, state = self.get_point_for_wb(world, game, hockeyist,  x_target, y_target)
            if speed_up > 0:
                accel = speed_up * k_f
            else:
                accel = speed_up * k_b
            hockeyist.speed_x += - hockeyist.speed_x * MyStrategy.k_abr + accel * cos(hockeyist.angle)
            hockeyist.speed_y += - hockeyist.speed_y * MyStrategy.k_abr + accel * sin(hockeyist.angle)
            hockeyist.x += hockeyist.speed_x
            hockeyist.y += hockeyist.speed_y
            if abs(turn) > turn_angle:
                hockeyist.angle += turn_angle*copysign(1.0, turn)
            else:
                hockeyist.angle += turn
            i += 1
            if state == True:
                return i
        return -1

    def nearest_own_to_point_not_selected_seeker(self, world, game, x_ct, y_ct):
        puck = world.puck
        puck_x, puck_y = self.ct(world, game, puck.x, puck.y)
        own_player = world.get_my_player()
        x_ct, y_ct = self.ct_inv(world, game, x_ct, y_ct)
        min_dist = 10000
        seeker_index, min_ticks = self.select_seeker(world, game, puck_x, puck_y)
        for hockeyist in world.hockeyists:
            if hockeyist.player_id == own_player.id and hockeyist.type != HockeyistType.GOALIE and hockeyist.teammate_index != seeker_index and hockeyist.state !=3:
                cur_dist = hypot(hockeyist.x - x_ct, hockeyist.y - y_ct)
                if min_dist > cur_dist:
                    min_dist = cur_dist
                    nearest_own_to_point_not_seeker = hockeyist.teammate_index
        return nearest_own_to_point_not_seeker, seeker_index, min_ticks

    def select_seeker(self, world, game, x_target, y_target):
        own_player = world.get_my_player()
        min_ticks = 1000
        for hockeyist in world.hockeyists:
            if hockeyist.player_id == own_player.id and hockeyist.type != HockeyistType.GOALIE and hockeyist.state !=3:
                ticks = self.emul_move_for_wb(world, game, hockeyist, x_target, y_target)
                if min_ticks > ticks and ticks != -1:
                    min_ticks = ticks
                    seeker_index = hockeyist.teammate_index
        if min_ticks == 1000:
            seeker_index = self.nearest_own_to_point(world, game, x_target, y_target)  
        return seeker_index, min_ticks

    def ct(self, world, game, x_in, y_in):
        opp_player = world.get_opponent_player()
        if opp_player.net_back > game.world_width/2.0:
            x = x_in - (game.rink_left + game.rink_right)/2.0
            y = - y_in + (game.rink_top + game.rink_bottom)/2.0
        else:
            x = - x_in + (game.rink_left + game.rink_right)/2.0
            y = - y_in + (game.rink_top + game.rink_bottom)/2.0
        return x, y

    def ct_speed(self, world, game, speed_x_in, speed_y_in):
        opp_player = world.get_opponent_player()
        if opp_player.net_back > game.world_width/2.0:
            speed_x = speed_x_in
            speed_y = - speed_y_in
        else:
            speed_x = - speed_x_in
            speed_y = - speed_y_in
        return speed_x, speed_y

    def ct_inv(self, world, game, x_in, y_in):
        opp_player = world.get_opponent_player()
        if opp_player.net_back > game.world_width/2.0:
            x = x_in + (game.rink_left + game.rink_right)/2.0
            y = -y_in + (game.rink_top + game.rink_bottom)/2.0
        else:
            x = - x_in + (game.rink_left + game.rink_right)/2.0
            y = - y_in + (game.rink_top + game.rink_bottom)/2.0
        return x, y

    def ct_inv_speed(self, world, game, speed_x_in, speed_y_in):
        opp_player = world.get_opponent_player()
        if opp_player.net_back > game.world_width/2.0:
            speed_x = speed_x_in
            speed_y = - speed_y_in
        else:
            speed_x = - speed_x_in
            speed_y = - speed_y_in
        return speed_x, speed_y

    def nearest_opp_to_point(self, world, game, x_ct, y_ct):
        own_player = world.get_my_player()
        x_ct, y_ct = self.ct_inv(world, game, x_ct, y_ct)
        min_dist = 10000
        for hockeyist in world.hockeyists:
            if hockeyist.player_id != own_player.id and hockeyist.type != HockeyistType.GOALIE and hockeyist.state !=3:
                cur_dist = hypot(hockeyist.x - x_ct, hockeyist.y - y_ct)
                if min_dist > cur_dist:
                    min_dist = cur_dist
                    nearest_opp = hockeyist.teammate_index
        return nearest_opp

    def nearest_own_to_point(self, world, game, x_ct, y_ct):
        own_player = world.get_my_player()
        x_ct, y_ct = self.ct_inv(world, game, x_ct, y_ct)
        min_dist = 10000
        for hockeyist in world.hockeyists:
            if hockeyist.player_id == own_player.id and hockeyist.type != HockeyistType.GOALIE and hockeyist.state !=3:
                cur_dist = hypot(hockeyist.x - x_ct, hockeyist.y - y_ct)
                if min_dist > cur_dist:
                    min_dist = cur_dist
                    nearest_own = hockeyist.teammate_index
        return nearest_own

    def nearest_own_to_point_not_me(self, world, game, me, x_ct, y_ct):
        own_player = world.get_my_player()
        x_ct, y_ct = self.ct_inv(world, game, x_ct, y_ct)
        min_dist = 10000
        for hockeyist in world.hockeyists:
            if hockeyist.player_id == own_player.id and hockeyist.type != HockeyistType.GOALIE and hockeyist.teammate_index != me.teammate_index and hockeyist.state !=3:
                cur_dist = hypot(hockeyist.x - x_ct, hockeyist.y - y_ct)
                if min_dist > cur_dist:
                    min_dist = cur_dist
                    nearest_own_not_me = hockeyist.teammate_index
        return nearest_own_not_me

    def nearest_own_to_point_not_puck_owner(self, world, game, x_ct, y_ct):
        puck = world.puck
        own_player = world.get_my_player()
        x_ct, y_ct = self.ct_inv(world, game, x_ct, y_ct)
        min_dist = 10000
        for hockeyist in world.hockeyists:
            if hockeyist.player_id == own_player.id and hockeyist.type != HockeyistType.GOALIE and hockeyist.id != puck.owner_hockeyist_id and hockeyist.state !=3:
                cur_dist = hypot(hockeyist.x - x_ct, hockeyist.y - y_ct)
                if min_dist > cur_dist:
                    min_dist = cur_dist
                    nearest_own_to_point_not_puck_owner = hockeyist.teammate_index
        return nearest_own_to_point_not_puck_owner

    def nearest_own_to_point_not_def(self, world, game, x_ct, y_ct):
        puck = world.puck
        own_player = world.get_my_player()
        x_ct, y_ct = self.ct_inv(world, game, x_ct, y_ct)
        min_dist = 10000
        def_index = self.nearest_own_to_point(world, game, MyStrategy.net_pos_x_mid, MyStrategy.net_pos_y_mid)
        for hockeyist in world.hockeyists:
            if hockeyist.player_id == own_player.id and hockeyist.type != HockeyistType.GOALIE and hockeyist.teammate_index !=def_index and hockeyist.state !=3: #and hockeyist.id != puck.owner_hockeyist_id 
                cur_dist = hypot(hockeyist.x - x_ct, hockeyist.y - y_ct)
                if min_dist > cur_dist:
                    min_dist = cur_dist
                    nearest_own_to_point_not_def = hockeyist.teammate_index
        return nearest_own_to_point_not_def

    def nearest_own_to_point_not_seeker(self, world, game, x_ct, y_ct):
        puck = world.puck
        puck_x, puck_y = self.ct(world, game, puck.x, puck.y)
        own_player = world.get_my_player()
        x_ct, y_ct = self.ct_inv(world, game, x_ct, y_ct)
        min_dist = 10000
        seeker_index = self.nearest_own_to_point(world, game, puck_x, puck_y)
        for hockeyist in world.hockeyists:
            if hockeyist.player_id == own_player.id and hockeyist.type != HockeyistType.GOALIE and hockeyist.teammate_index != seeker_index and hockeyist.state !=3: #and hockeyist.id != puck.owner_hockeyist_id 
                cur_dist = hypot(hockeyist.x - x_ct, hockeyist.y - y_ct)
                if min_dist > cur_dist:
                    min_dist = cur_dist
                    nearest_own_to_point_not_seeker = hockeyist.teammate_index
        return nearest_own_to_point_not_seeker

    def nearest_opp_to_point_not_puck_owner(self, world, game, x_ct, y_ct):
        puck = world.puck
        opp_player = world.get_opponent_player()
        x_ct, y_ct = self.ct_inv(world, game, x_ct, y_ct)
        min_dist = 10000
        for hockeyist in world.hockeyists:
            if hockeyist.player_id == opp_player.id and hockeyist.type != HockeyistType.GOALIE and hockeyist.id != puck.owner_hockeyist_id and hockeyist.state !=3:
                cur_dist = hypot(hockeyist.x - x_ct, hockeyist.y - y_ct)
                if min_dist > cur_dist:
                    min_dist = cur_dist
                    nearest_opp_to_point_not_puck_owner = hockeyist.teammate_index
        return nearest_opp_to_point_not_puck_owner

    def opp_index(self, world, game, index):
        own_player = world.get_my_player()
        for hockeyist in world.hockeyists:
            if hockeyist.player_id != own_player.id and hockeyist.teammate_index == index:
                x, y = self.ct(world, game, hockeyist.x, hockeyist.y)
                speed_x, speed_y = self.ct_speed(world, game, hockeyist.speed_x, hockeyist.speed_y)
                return x, y, speed_x, speed_y

    def own_index(self, world, game, index):
        own_player = world.get_my_player()
        for hockeyist in world.hockeyists:
            if hockeyist.player_id == own_player.id and hockeyist.teammate_index == index:
                x, y = self.ct(world, game, hockeyist.x, hockeyist.y)
                speed_x, speed_y = self.ct_speed(world, game, hockeyist.speed_x, hockeyist.speed_y)
                return x, y, speed_x, speed_y

    def normalize(self, x, y):
        x_norm = x / hypot(x, y)
        y_norm = y / hypot(x, y)
        return x_norm, y_norm

    def distant_to_opp(self, world, game, me):
        state = False
        own_player = world.get_my_player()
        opp_player = world.get_opponent_player()
        max_dist = 0.0
        for hockeyist_own in world.hockeyists:
            if hockeyist_own.player_id == own_player.id and hockeyist_own.type != HockeyistType.GOALIE and hockeyist.state !=3:
                cur_dist_tot = 0.0
                for hockeyist_opp in world.hockeyists:
                    if hockeyist_opp.player_id == opp_player.id and hockeyist_opp.type != HockeyistType.GOALIE:
                        cur_dist = hypot(hockeyist_own.x - hockeyist_opp.x, hockeyist_own.y - hockeyist_opp.y)
                        cur_dist_tot = cur_dist_tot + cur_dist
                if max_dist < cur_dist_tot:
                    max_dist = cur_dist_tot
                    distant_to_opp = hockeyist_own.teammate_index
                    if hockeyist_own.teammate_index == me.teammate_index:
                        state = False
                    else:
                        state = True
        return distant_to_opp, state

    def check_opp_strike(self, world, game, me, check_opp_index):
        opp_player = world.get_opponent_player()
        state_angle = False
        state_dist = False
        state = False
        x_down, y_down = self.ct_inv(world, game, -MyStrategy.strike_target_x, MyStrategy.strike_target_y)
        x_up, y_up = self.ct_inv(world, game, -MyStrategy.strike_target_x, -MyStrategy.strike_target_y)
        for hockeyist_opp in world.hockeyists:
            if hockeyist_opp.player_id == opp_player.id and hockeyist_opp.type != HockeyistType.GOALIE and hockeyist.state !=3:
                if hockeyist_opp.teammate_index == check_opp_index:
                    angle_down = hockeyist_opp.get_angle_to(x_down, y_down)
                    angle_up = hockeyist_opp.get_angle_to(x_up, y_up)
                    if abs(angle_up) < MyStrategy.STRIKE_ANGLE or abs(angle_down) < MyStrategy.STRIKE_ANGLE:
                        state_angle = True
        puck = world.puck
        puck_x, puck_y = self.ct(world, game, puck.x, puck.y)
        me_x, me_y = self.ct(world, game, me.x, me.y)
        opp_x, opp_y, opp_speed_x, opp_speed_y = self.opp_index(world, game, check_opp_index)
        if hypot(puck_x - opp_x, puck_y - opp_y) < game.stick_length*1.5:
            state_dist = True
        if state_dist == True and state_angle == True:
            state = True
        return state

    def subs(self, world, game, me):
        puck = world.puck
        puck_x, puck_y = self.ct(world, game, puck.x, puck.y)
        me_x, me_y = self.ct(world, game, me.x, me.y)
        own_player = world.get_my_player()
        if ((me.stamina < 700 and puck_x > 0 and me_x < 0 and me_y > 0 and puck.owner_hockeyist_id != me.id) or ((own_player.just_scored_goal or own_player.just_missed_goal) and me.stamina < 1500)):
            return True
        if me.stamina < 900 and puck_x > MyStrategy.pass_back and me_x < 0:
            return True
        return False

    def subs_index(self, world, game, me):
        own_player = world.get_my_player()
        stamina_min = 0
        for h in world.hockeyists:
            if h.state == 3 and h.player_id == own_player.id:
                if h.stamina > stamina_min:
                    index = h.teammate_index
                    stamina_min = h.stamina
        return index

    def own_index_obj(self, world, game, index):
        own_player = world.get_my_player()
        for hockeyist in world.hockeyists:
            if hockeyist.player_id == own_player.id and hockeyist.teammate_index == index:
                return hockeyist



#================================================PHYSICAL FUNCTIONS=======================================================

#arrival behavior (forward and backward, selection between them), predicting coordinates.

    def get_point_for(self, world, game, me, x_target, y_target):
        k_f = game.hockeyist_speed_up_factor * (me.agility*0.75 + me.agility*0.25*me.stamina/2000.0)/ 100 
        k_b = game.hockeyist_speed_down_factor * (me.agility*0.75 + me.agility*0.25*me.stamina/2000.0) / 100
        accuracy = 7*k_f/MyStrategy.k_abr
        accuracy_v = 1.9*k_f
        turn = 0.0
        speed_up = 0.0
        state = False
        reversal_angle = pi/2.0
        puck = world.puck
        x, y = self.ct_inv(world, game, x_target, y_target)
        angle_to_target = me.get_angle_to(x, y)     
        angle_to_velocity = me.get_angle_to(me.speed_x + me.x, me.speed_y + me.y)                          
        x, y = self.ct(world, game, me.x, me.y) 
        S_act =  hypot(x - x_target, y - y_target)
        V_0_proj = cos(angle_to_velocity)*hypot(me.speed_x, me.speed_y)
        if cos(angle_to_velocity) > 0:
            T_proj = - (1.0 / MyStrategy.k_abr) * log(k_b/(MyStrategy.k_abr*V_0_proj + k_b))
        else:
            T_proj = 10000
        S_prob = V_0_proj / MyStrategy.k_abr - k_b / MyStrategy.k_abr * T_proj
        if S_act > accuracy:
            #speed correction
            if S_prob < S_act:
                speed_up = 1.0
            elif S_prob > S_act:
                speed_up = -1.0
            if pi >= abs(angle_to_target) >= 2.0*pi/3.0:
                speed_up = -1.0
            elif 2.0*pi/3.0 >= abs(angle_to_target) >= pi/3.0:
                speed_up = 0.0
            #angle correction in case of significant deviation
            turn = angle_to_target
            if reversal_angle > abs(angle_to_target - angle_to_velocity) > game.hockeyist_turn_angle_factor and V_0_proj > 0:
                turn = turn + copysign(1.0, speed_up)*(-angle_to_velocity + angle_to_target)
        if S_act < accuracy and V_0_proj >= accuracy_v:
            speed_up, angle = self.brakes(me, world)  
            turn = angle
        elif S_act < accuracy and V_0_proj < accuracy_v:
            speed_up = 0
            turn = me.get_angle_to(puck.x, puck.y)
            state = True        
        return speed_up, turn, S_act, state

    def get_point_for_wb(self, world, game, me, x_target, y_target):
        k_f = game.hockeyist_speed_up_factor * (me.agility*0.75 + me.agility*0.25*me.stamina/2000.0) / 100
        k_b = game.hockeyist_speed_down_factor * (me.agility*0.75 + me.agility*0.25*me.stamina/2000.0) / 100
        accuracy = game.stick_length/2.0
        accuracy_v = 0.0
        turn = 0.0
        speed_up = 0.0
        state = False
        reversal_angle = pi/2.0
        puck = world.puck
        x, y = self.ct_inv(world, game, x_target, y_target)
        angle_to_target = me.get_angle_to(x, y)     
        angle_to_velocity = me.get_angle_to(me.speed_x + me.x, me.speed_y + me.y)                          
        x, y = self.ct(world, game, me.x, me.y) 
        S_act =  hypot(x - x_target, y - y_target)
        V_0_proj = cos(angle_to_velocity)*hypot(me.speed_x, me.speed_y)
        S_prob = 0
        if S_act > accuracy:
            #speed correction
            if S_prob < S_act:
                speed_up = 1.0
            elif S_prob > S_act:
                speed_up = -1.0
            if pi >= abs(angle_to_target) >= 2.0*pi/3.0:
                speed_up = -1.0
            elif 2.0*pi/3.0 >= abs(angle_to_target) >= pi/3.0:
                speed_up = 0.0
            #angle correction in case of significant deviation
            turn = angle_to_target
            if reversal_angle > abs(angle_to_target - angle_to_velocity) > game.hockeyist_turn_angle_factor and V_0_proj > 0:
                turn = turn + copysign(1.0, speed_up)*(-angle_to_velocity + angle_to_target) 
        if S_act < accuracy:
            speed_up = 0.0
            turn = me.get_angle_to(puck.x, puck.y)
            state = True
        return speed_up, turn, S_act, state

    def get_point_rev(self, world, game, me, x_target, y_target):
        k_f = game.hockeyist_speed_up_factor * (me.agility*0.75 + me.agility*0.25*me.stamina/2000.0) / 100
        k_b = game.hockeyist_speed_down_factor * (me.agility*0.75 + me.agility*0.25*me.stamina/2000.0) / 100
        accuracy = 7*k_f/MyStrategy.k_abr
        accuracy_v = 1.9*k_f
        reversal_angle = pi/2.0
        turn = 0.0
        speed_up = 0.0
        state = False
        puck = world.puck
        x, y = self.ct_inv(world, game, x_target, y_target)
        if me.get_angle_to(x, y) >= 0:
            angle_to_target = me.get_angle_to(x, y) - pi  
        else:
            angle_to_target = me.get_angle_to(x, y) + pi                              
        x, y = self.ct(world, game, me.x, me.y) 
        S_act =  hypot(x - x_target, y - y_target)
        if me.get_angle_to(me.speed_x + me.x, me.speed_y + me.y) >= 0:
            angle_to_velocity = me.get_angle_to(me.speed_x + me.x, me.speed_y + me.y) - pi  
        else:
            angle_to_velocity = me.get_angle_to(me.speed_x + me.x, me.speed_y + me.y) + pi   
        V_0_proj = cos(angle_to_velocity)*hypot(me.speed_x, me.speed_y)
        if cos(angle_to_velocity) > 0:
            T_proj = - (1.0 / MyStrategy.k_abr) * log(k_f/(MyStrategy.k_abr*V_0_proj + k_f))
        else:
            T_proj = 1000000
        S_prob = V_0_proj / MyStrategy.k_abr - k_f / MyStrategy.k_abr * T_proj
        if S_act > accuracy:
            #speed correction
            if S_prob > S_act:
                speed_up = 1.0
            else:
                speed_up = -1.0 
            if abs(angle_to_target) >= reversal_angle:
                speed_up = 1.0
            #angle correction in case of significant deviation
            turn = angle_to_target
            if reversal_angle > abs(angle_to_target - angle_to_velocity) > game.hockeyist_turn_angle_factor and V_0_proj > 0:
                turn = turn - copysign(1.0, speed_up)*(-angle_to_velocity + angle_to_target)
        if S_act < accuracy and V_0_proj >= accuracy_v:
            speed_up, angle = self.brakes(me, world)  
            turn = angle
        elif S_act < accuracy and V_0_proj < accuracy_v:            
            speed_up = 0
            turn = me.get_angle_to(puck.x, puck.y)
            state = True
        return speed_up, turn, S_act, state

    def brakes(self, me, world):
        angle_velocity = -me.get_angle_to(me.speed_x + me.x, me.speed_y + me.y)
        if abs(angle_velocity) > pi/2.0:
            if angle_velocity < 0.0:
                angle = pi + angle_velocity
            else:
                angle = angle_velocity - pi
            return 1.0, angle
        else:
            angle = -angle_velocity
            return -1.0, angle

    def predict_coords(self, game, me, x, y, speed_x, speed_y):
        #not universal coordinates are used
        T = hypot(x - me.x, y - me.y) / min((game.hockeyist_max_speed,(hypot(me.speed_x, me.speed_y) + MyStrategy.prediction_coords_velocity)))
        if  hypot(x - me.x, y - me.y) < game.stick_length:
            T = 0.0
        x = x + speed_x * T
        y = y + speed_y * T
        return x, y

    def predict_coords_pass(self, game, me, v0, x, y, speed_x, speed_y):
        #not universal coordinates are used
        dist = hypot(x - me.x, y - me.y)
        #to prevent negative numbers in logarithm
        if MyStrategy.k_abr*dist/v0 > 1:
            v0 = MyStrategy.k_abr*dist*10
        time = -(1.0/MyStrategy.k_abr)*log(1-MyStrategy.k_abr*dist/v0)        
        x = x + speed_x/MyStrategy.k_abr * (1 - exp(-MyStrategy.k_abr*time))
        y = y + speed_y/MyStrategy.k_abr * (1 - exp(-MyStrategy.k_abr*time))
        return x, y

#****************************************************POTENTIALS*****************************************************************

    def get_force_x_y(self, world, game, me, sign, target_x, target_y):
        sign = 1.0
        force_factor = 5000.0
        me_x, me_y = self.ct(world, game, me.x, me.y)
        force_opp_x, force_opp_y = self.force_opp(world, game, me, sign)
        force_own_x, force_own_y = self.force_own(world, game, me, sign)
        force_target_x, force_target_y = self.force_target(world, game, me, target_x, target_y)
        force_walls_x, force_walls_y = self.force_walls(world, game, me)
        force_def_point_1_x, force_def_point_1_y = self.force_point(world, game, me, 1.0, pi, 240000.0, 0.0, 0.0, -((game.rink_left + game.rink_right)/2.0 - game.rink_left), (game.rink_top + game.rink_bottom)/2.0 - game.rink_top)
        force_def_point_2_x, force_def_point_2_y = self.force_point(world, game, me, 1.0, pi, 240000.0, 0.0, 0.0, -((game.rink_left + game.rink_right)/2.0 - game.rink_left), -(game.rink_bottom - (game.rink_top + game.rink_bottom)/2.0))
        force_def_point_0_x, force_def_point_0_y = self.force_point(world, game, me, 1.0, pi, 240000.0, 0.0, 0.0, -((game.rink_left + game.rink_right)/2.0 - game.rink_left), 0.0)
        x = me_x + force_opp_x * force_factor + force_own_x * force_factor + force_target_x * force_factor + force_walls_x * force_factor + force_def_point_1_x * force_factor + force_def_point_2_x * force_factor + force_def_point_0_x * force_factor
        y = me_y + force_opp_y * force_factor + force_own_y * force_factor + force_target_y * force_factor + force_walls_y * force_factor + force_def_point_1_y * force_factor + force_def_point_2_y * force_factor + force_def_point_0_y * force_factor
        return x, y

    def force_opp(self, world, game, me, sign):
        #force coeffs
        normalized_dist = 45.0
        c_2 = 40.0
        cc_2 = 40.0
        c_6 = 0.0
        cc_6 = 0.0
        c_0 = 0.0
        shift_opp_angle = pi/1.0
        #end of force coeffs
        force_x = 0.0
        force_y = 0.0
        opp_player = world.get_opponent_player()
        me_x, me_y = self.ct(world, game, me.x, me.y)
        me_speed_x, me_speed_y = self.ct_speed(world, game, me.speed_x, me.speed_y)
        for hockeyist in world.hockeyists:
            if hockeyist.player_id == opp_player.id and hockeyist.type != HockeyistType.GOALIE and hockeyist.state != 3:
                opp_x_ct, opp_y_ct, opp_speed_x_ct, opp_speed_y_ct = self.opp_index(world, game, hockeyist.teammate_index)
                dist = hypot(me_x - opp_x_ct, me_y - opp_y_ct)
                #that's a simplification for speed
                #r1 instead of r2
                speed = -cos(shift_opp_angle)*hypot(me_speed_x, me_speed_y) + hypot(opp_speed_x_ct, opp_speed_y_ct)
                force_opp = (c_2*speed+cc_2)/(dist-normalized_dist)**1 + (c_6*speed+cc_6)/(dist-normalized_dist)**6 + c_0
                me_opp_x = opp_x_ct - me_x
                me_opp_y = opp_y_ct - me_y
                # when sign = 1, clockwise
                vec_x = cos(shift_opp_angle)*me_opp_x + sin(shift_opp_angle)*me_opp_y*sign
                vec_y = -sin(shift_opp_angle)*me_opp_x*sign + cos(shift_opp_angle)*me_opp_y                
                vec_x, vec_y = self.normalize(vec_x, vec_y) 
                me_opp_x, me_opp_y = self.normalize(me_opp_x, me_opp_y)                                
                vec_x = vec_x * force_opp
                vec_y = vec_y * force_opp
                if opp_x_ct < me_x:
                    vec_x = 0.0
                    vec_y = 0.0
                force_x = force_x + vec_x
                force_y = force_y + vec_y
        return force_x, force_y

    def force_own(self, world, game, me, sign):
        #force coeffs
        normalized_dist = 45.0
        c_2 = 20.0
        cc_2 = 20.0
        c_6 = 0.0
        cc_6 = 0.0
        c_0 = 0.0
        shift_own_angle = pi/1.0
        #end of force coeffs
        force_x = 0.0
        force_y = 0.0
        own_player = world.get_my_player()
        me_x, me_y = self.ct(world, game, me.x, me.y)
        me_speed_x, me_speed_y = self.ct_speed(world, game, me.speed_x, me.speed_y)
        for hockeyist in world.hockeyists:
            if hockeyist.player_id == own_player.id and hockeyist.type != HockeyistType.GOALIE and me.teammate_index != hockeyist.teammate_index and hockeyist.state != 3:
                own_x_ct, own_y_ct, own_speed_x_ct, own_speed_y_ct = self.own_index(world, game, hockeyist.teammate_index)
                dist = hypot(me_x - own_x_ct, me_y - own_y_ct)
                #that's a simplification for speed
                #r1 instead of r2
                speed = -cos(shift_own_angle)*hypot(me_speed_x, me_speed_y) + hypot(own_speed_x_ct, own_speed_y_ct)
                force_own = (c_2*speed+cc_2)/(dist-normalized_dist)**1 + (c_6*speed+cc_6)/(dist-normalized_dist)**6 + c_0
                me_own_x = own_x_ct - me_x
                me_own_y = own_y_ct - me_y
                # when sign = 1, clockwise
                vec_x = cos(shift_own_angle)*me_own_x + sin(shift_own_angle)*me_own_y*sign
                vec_y = -sin(shift_own_angle)*me_own_x*sign + cos(shift_own_angle)*me_own_y                
                vec_x, vec_y = self.normalize(vec_x, vec_y) 
                me_own_x, me_own_y = self.normalize(me_own_x, me_own_y)                                
                vec_x = vec_x * force_own
                vec_y = vec_y * force_own
                if own_x_ct < me_x:
                    vec_x = 0.0
                    vec_y = 0.0
                force_x = force_x + vec_x
                force_y = force_y + vec_y
        return force_x, force_y

    def force_target(self, world, game, me, target_x, target_y):
        #attractive force for target is constant
        force_x = 0.0
        force_y = 0.0
        c_0 = 20.00
        me_x, me_y = self.ct(world, game, me.x, me.y)
        #me_speed_x = me.speed_x
        #me_speed_y = - me.speed_y
        dist = hypot(me_x - target_x, me_y - target_y)
        me_target_x = target_x - me_x
        me_target_y = target_y - me_y              
        vec_x, vec_y = self.normalize(me_target_x, me_target_y)                           
        force_x = vec_x * c_0
        force_y = vec_y * c_0
        return force_x, force_y

    def force_walls(self, world, game, me):
        #force coeffs
        normalized_dist = 20.0
        c_2 = 0.0
        cc_2 = 0.0
        c_6 = 0.0
        cc_6 = 10000000000.0
        c_0 = 0.0
        #end of force coeffs
        force_x = 0.0
        force_y = 0.0
        speed = 0.0
        me_x, me_y = self.ct(world, game, me.x, me.y)
        top_wall_y = (game.rink_top + game.rink_bottom)/2.0 - game.rink_top
        bottom_wall_y = - (game.rink_bottom - (game.rink_top + game.rink_bottom)/2.0)
        left_wall_x = -((game.rink_left + game.rink_right)/2.0 - game.rink_left)
        dist1 = top_wall_y - me_y
        dist2 = me_y - bottom_wall_y
        dist3 = me_x - left_wall_x
        force_top_wall = (c_2*speed+cc_2)/(dist1-normalized_dist)**2 + (c_6*speed+cc_6)/(dist1-normalized_dist)**6 + c_0
        force_bottom_wall = (c_2*speed+cc_2)/(dist2-normalized_dist)**2 + (c_6*speed+cc_6)/(dist2-normalized_dist)**6 + c_0
        force_left_wall = (c_2*speed+cc_2)/(dist3-normalized_dist)**2 + (c_6*speed+cc_6)/(dist3-normalized_dist)**6 + c_0
        vec_x = 1.0 * force_left_wall
        vec_y = -1.0 * force_top_wall + 1.0 * force_bottom_wall   
        force_x = vec_x
        force_y = vec_y
        return force_x, force_y

    def force_point(self, world, game, me, sign, shift_point_angle, cc_2, cc_6, c_0, x, y):
        #force coeffs
        normalized_dist = 20.0
        c_2 = 0.0
        c_6 = 0.0
        #end of force coeffs
        force_x = 0.0
        force_y = 0.0
        me_x, me_y = self.ct(world, game, me.x, me.y)
        #me_speed_x = me.speed_x
        #me_speed_y = - me.speed_y
        dist = hypot(me_x - x, me_y - y)
        speed = 0.0
        force_point = (c_2*speed+cc_2)/(dist-normalized_dist)**2 + (c_6*speed+cc_6)/(dist-normalized_dist)**6 + c_0
        me_point_x = x - me_x
        me_point_y = y - me_y
        # when sign = 1, clockwise
        vec_x = cos(shift_point_angle)*me_point_x + sin(shift_point_angle)*me_point_y*sign
        vec_y = -sin(shift_point_angle)*me_point_x*sign + cos(shift_point_angle)*me_point_y                
        vec_x, vec_y = self.normalize(vec_x, vec_y) 
        me_point_x, me_point_y = self.normalize(me_point_x, me_point_y)                                
        vec_x = vec_x * force_point
        vec_y = vec_y * force_point
        force_x = force_x + vec_x
        force_y = force_y + vec_y
        return force_x, force_y


