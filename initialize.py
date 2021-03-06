#!/usr/bin/python
from evtk.hl import gridToVTK
from geometry import create_grid
import numpy as np
from boundary_conditions import set_other_variables


def set_starting_values(primary_variables):
    return primary_variables

# Generate an initial flow solution based off the flow conditions and the geometry
def initial_setup(nu, nv, nw):
    #--------------------------------------------------------------
    #
    # Read in the boundary conditions file and save variables
    #
    #--------------------------------------------------------------

    # Read in boundary condition file!
    bcfile = open('boundary_conditions.txt', 'r')
    input_data = bcfile.readlines()
    bcfile.close()

    # Skip the header and proceed with the initialization!
    line_2 = input_data[1].split()
    rgas = np.float(line_2[2])

    line_3 = input_data[2].split()
    gamma = np.float(line_3[2])

    line_4 = input_data[3].split()
    pressure_stag_inlet = np.float(line_4[2])

    line_5 = input_data[4].split()
    temp_stag_inlet = np.float(line_5[2])

    line_6 = input_data[5].split()
    alpha_1 = np.float(line_6[2])

    line_7 = input_data[6].split()
    pressure_static_exit = np.float(line_7[2])

    line_8 = input_data[7].split()
    cfl = np.float(line_8[2])

    line_9 = input_data[8].split()
    smooth_fac_input = np.float(line_9[2])

    line_10 = input_data[9].split()
    nsteps = np.float(line_10[2])

    line_11 = input_data[10].split()
    conlim_in = np.float(line_11[2])

    boundary_conditions = [rgas, gamma, pressure_stag_inlet, temp_stag_inlet, alpha_1, pressure_static_exit, cfl ,  smooth_fac_input, nsteps, conlim_in ]

    #----------------------------------------------
    #
    # Setup other variables!
    #
    #----------------------------------------------
    cp = rgas * gamma / (gamma - 1.0)
    cv = cp / (gamma * 1.0)
    gamma_factor = (gamma - 1.0) / (gamma * 1.0)

    #----------------------------------------------
    #
    # Here we initialize the flow variables!
    #
    #-----------------------------------------------
    ro = np.zeros((nv, nu, nw)) # Density
    ro_vel_x = np.zeros((nv, nu, nw)) # Density * Velocity in "x" direction
    ro_vel_y = np.zeros((nv, nu, nw)) # Density * Velocity in "y" direction
    pressure = np.zeros((nv, nu, nw)) # static pressure
    ro_energy = np.zeros((nv, nu, nw)) # Density * energy
    vel_x = np.zeros((nv, nu, nw)) # velocity-x
    vel_y = np.zeros((nv, nu, nw)) # velocity-y
    enthalpy_stag = np.zeros((nv, nu, nw)) # Stagnation enthalpy

    #----------------------------------------------
    #
    # Here we initialize the fluxes!
    #
    #-----------------------------------------------
    flux_i_mass = np.zeros((nv, nu)) # Mass
    flux_j_mass = np.zeros((nv, nu))

    flux_i_xmom = np.zeros((nv, nu)) # X-MOMENTUM
    flux_j_xmom = np.zeros((nv, nu))

    flux_i_ymom = np.zeros((nv, nu)) # Y-MOMENTUM
    flux_j_ymom = np.zeros((nv, nu))

    flux_i_enthalpy = np.zeros((nv, nu)) # Enthalpy
    flux_j_enthalpy = np.zeros((nv, nu))

    flow = np.zeros((nu, 1)) # total mass flow rate across each "i"

    #----------------------------------------------
    #
    # new guess subroutine
    #
    #-----------------------------------------------
    jmid = nv / 2.0
    temp_static_exit = temp_stag_inlet * (pressure_static_exit/pressure_stag_inlet)**gamma_factor
    vel_exit = np.sqrt(2 * cp * (temp_stag_inlet - temp_static_exit))
    ro_exit = pressure_static_exit / rgas / temp_static_exit
    pressure_static_inlet = 55000
    temp_static_inlet = temp_stag_inlet * (pressure_static_inlet / pressure_stag_inlet)**gamma_factor
    vel_inlet = np.sqrt(2 * cp * (temp_stag_inlet - temp_static_inlet))
    ro_inlet = pressure_static_inlet / rgas / temp_static_inlet

    # Get the grid!
    grid_parameters = create_grid(nu, nv, nw)
    point_x = grid_parameters[0]
    point_y = grid_parameters[1]
    point_z = grid_parameters[2]

    # Initial guess!
    for j in range(0, nv):
        for i in range(0, nu):
            ro[j,i,0] = 1.2
            ro_vel_x[j,i,0] = 100 * (i * 1.0)/(nu * 1.0)
            ro_vel_y[j,i,0] = 0.0
            pressure[j,i,0] = 100000 * (0.9 + 0.1 * (i * 1.0)/(nu * 1.0))
            enthalpy_stag[j,i,0] = 300000
            ro_energy[j,i,0] = pressure[j,i,0] / (gamma - 1.0)


    for j in range(0, nv):
        for i in range(0, nu-1):
            dx = point_x[jmid, i+1, 0] - point_x[jmid, i, 0]
            dy = point_y[jmid, i+1, 0] - point_y[jmid, i, 0]
            ds = np.sqrt(dx*dx + dy*dy)

            vel_local = vel_inlet + (vel_exit - vel_inlet)* (1.0 * (i-1.0)/(nu - 1.0) )
            ro_local = ro_inlet + (ro_exit - ro_inlet)* (1.0 * (i-1.0)/(nu - 1.0) )
            temp_local = temp_static_inlet + (temp_static_exit - temp_static_inlet)* (1.0 * (i-1.0)/(nu - 1.0) )


            velx = vel_local * dx / ds
            vely = vel_local * dy / ds

            ro_vel_x[j,i,0] = ro_local * velx
            ro_vel_y[j,i,0] = ro_local * vely
            ro[j,i,0] = ro_local
            ro_energy[j,i,0] = ro_local * (cv * temp_local + 0.5 * vel_local * vel_local)

        ro_vel_x[j,nu-1,0] = ro_vel_x[j,nu-2,0]
        ro_vel_y[j,nu-1,0] = ro_vel_y[j,nu-2,0]
        ro[j,nu-1,0] = ro[j,nu-2,0]
        ro_energy[j,nu-1,0] = ro_energy[j,nu-2,0]


    #-------------------------------------------------------------------------
    #
    # Output initial flow solution with grid
    #
    #-------------------------------------------------------------------------
    gridToVTK("./initial_flow", point_x, point_y, point_z, pointData={"pressure": pressure, "density": ro, "density-velx": ro_vel_x })

    #-------------------------------------------------------------------------
    #
    # Setting primary & secondary flow variables
    #
    #-------------------------------------------------------------------------
    primary_variables = {}
    secondary_variables = {}
    primary_variables[0] = ro
    primary_variables[1] = ro_vel_x
    primary_variables[2] = ro_vel_y
    primary_variables[3] = ro_energy
    secondary_variables[0] = vel_x
    secondary_variables[1] = vel_y
    secondary_variables[2] = pressure
    secondary_variables[3] = enthalpy_stag

    #-------------------------------------------------------------------------
    #
    # Setting the fluxes
    #
    #-------------------------------------------------------------------------
    fluxes = {}
    fluxes[0] = flux_i_mass
    fluxes[1] = flux_j_mass
    fluxes[2] = flux_i_xmom
    fluxes[3] = flux_j_xmom
    fluxes[4] = flux_i_ymom
    fluxes[5] = flux_j_ymom
    fluxes[6] = flux_i_enthalpy
    fluxes[7] = flux_j_enthalpy
    fluxes[8] = flow

    secondary_variables = set_other_variables(primary_variables, secondary_variables, boundary_conditions, grid_parameters)

    return primary_variables, secondary_variables, fluxes, boundary_conditions, grid_parameters
