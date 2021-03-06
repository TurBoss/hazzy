#!/usr/bin/env python

#   Copyright (c) 2017 Kurt Jacobson
#      <kurtcjacobson@gmail.com>
#
#   This file is part of Hazzy.
#
#   Hazzy is free software: you can redistribute it and/or modify
#   it under the terms of the GNU General Public License as published by
#   the Free Software Foundation, either version 2 of the License, or
#   (at your option) any later version.
#
#   Hazzy is distributed in the hope that it will be useful,
#   but WITHOUT ANY WARRANTY; without even the implied warranty of
#   MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#   GNU General Public License for more details.
#
#   You should have received a copy of the GNU General Public License
#   along with Hazzy.  If not, see <http://www.gnu.org/licenses/>.

# Description:
#   Collection of linuxcnc.command convenience functions.
#   Incomplete

import linuxcnc
from utilities import ini_info
from utilities import notifications

num_joints = ini_info.get_num_joints()
no_force_homing = ini_info.get_no_force_homing()

# Setup logging
from utilities import logger
log = logger.get(__name__)

stat = linuxcnc.stat()
command = linuxcnc.command()

def estop():
    set_state(linuxcnc.STATE_ESTOP)

def estop_reset():
    set_state(linuxcnc.STATE_ESTOP_RESET)

def machine_off():
    set_state(linuxcnc.STATE_OFF)

def machine_on():
    set_state(linuxcnc.STATE_ON)

def mist_on():
    command.mist(1)

def mist_off():
    command.mist(0)

def flood_on():
    command.flood(1)

def flood_off():
    command.flood(0)

def auto_run(start_line=0):
    '''Run loaded program if OK to do so.'''

    stat.poll()
    msg = None
    if stat.estop:
        msg = "Can't run program when estoped"
    elif not stat.enabled:
        msg = "Can't run program when not enabled"
    elif not no_force_homing if no_force_homing else not is_homed():
        msg = "Can't run program when not homed"
    elif not stat.interp_state == linuxcnc.INTERP_IDLE:
        msg = "Can't run program when interpreter is not idle"
    elif stat.file == "":
        msg = "Can't run program when no file loaded"
    else:
        set_mode(linuxcnc.MODE_AUTO)
        command.auto(linuxcnc.AUTO_RUN, start_line)
        info = "Running the program '{}' from line {}".format(stat.file, start_line)
        notifications.show_success(info, "Program Started!")
        log.info(info)
    if msg:
        log.error(msg)
        notifications.show_error(msg)
        return msg

def abort():
    log.debug('Issuing abort command')
    command.abort()


def set_mode(mode):
    '''Set mode to one of
    linuxcnc.MODE_MANUAL
    linuxcnc.MODE_MDI
    linuxcnc.MODE_AUTO
    '''
    stat.poll()
    if stat.task_mode == mode:
        return
    command.mode(mode)
    command.wait_complete()

def set_state(state):
    '''Set state to one of
    linuxcnc.STATE_ESTOP
    linuxcnc.STATE_ESTOP_RESET
    linuxcnc.STATE_ON
    linuxcnc.STATE_OFF
    '''
    stat.poll()
    if stat.task_state == state:
        return
    command.state(state)
    command.wait_complete()

def set_motion_mode(mode):
    '''Set motion mode to one of
    linuxcnc.TRAJ_MODE_FREE
    linuxcnc.TRAJ_MODE_TELEOP
    linuxcnc.TRAJ_MODE_COORD
    '''
    stat.poll()
    if stat.motion_mode == mode:
        return
    command.teleop_enable(0)
    command.traj_mode(mode)
    command.wait_complete()

def load_file(fname):
    if stat.file != "":
        # Is this needed?
        set_mode(linuxcnc.MODE_MDI)
        set_mode(linuxcnc.MODE_AUTO)
    command.program_open(fname)

def issue_mdi(mdi_command):
    '''Issue an MDI command if OK to do so.'''
    stat.poll()
    if stat.estop:
        log.error("Can't issue MDI when estoped")
    elif not stat.enabled:
        log.error("Can't issue MDI when not enabled")
    elif not no_force_homing if no_force_homing else not is_homed():
        log.error("Can't issue MDI when not homed")
    elif not stat.interp_state == linuxcnc.INTERP_IDLE:
        log.error("Can't issue MDI when interpreter is not idle")
    else:
        # Lets do this!
        set_mode(linuxcnc.MODE_MDI)
        log.info("Issuing MDI command: {0}".format(mdi_command))
        command.mdi(mdi_command)
#        set_mode(linuxcnc.MODE_MANUAL) # This blocks??

def set_work_coordinate(axis, position):
    '''Set the current coordinates for `axis` to `position`.
    Args:
        axis (str): The axis for which to set the coordinates
        position (float): The desired new coordinates for the axis
    '''
    stat.poll()
    cmd = 'G10 L20 P{0:d} {1}{2:.12f}'.format(stat.g5x_index, axis.upper(), position)
    issue_mdi(cmd)
    set_mode(linuxcnc.MODE_MANUAL)

def home_joint(joint):
    '''Home/Unhome the specified joint, -1 for all.'''
    set_mode(linuxcnc.MODE_MANUAL)
    stat.poll()
    if not stat.estop and stat.enabled \
     and not stat.joint[joint]['homed'] and not stat.joint[joint]['homing']:
        log.info("Homing joint {0}".format(joint))
        command.home(joint)
    elif stat.joint[joint]['homed']:
        log.info("joint {0} is already homed, unhoming".format(joint))
        set_motion_mode(linuxcnc.TRAJ_MODE_FREE)
        command.unhome(joint)
    elif stat.joint[joint]['homing']:
        log.error("Homing sequence already in progress")
    else:
        log.error("Can't home joint {0}, check E-stop and machine power".format(joint))

def is_homed():
    '''Returns TRUE if all joints are homed.'''
    stat.poll()
    for joint in range(num_joints):
        if not stat.joint[joint]['homed']:
            return False
    return True

def is_moving():
    '''Returns TRUE if machine is moving due to MDI, program execution, etc.'''
    if stat.state == linuxcnc.RCS_EXEC:
        return True
    else:
        return stat.task_mode == linuxcnc.MODE_AUTO \
            and stat.interp_state != linuxcnc.INTERP_IDLE
