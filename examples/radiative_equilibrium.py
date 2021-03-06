from sympl import (
    DataArray, AdamsBashforth, PlotFunctionMonitor)
from climt import (
    Frierson06LongwaveOpticalDepth, GrayLongwaveRadiation)
import numpy as np
from datetime import timedelta

pressure_axis = np.array(
    [1e5, 9e4, 8e4, 7e4, 5e4, 3e4, 1e4, 8e3, 4e3, 1e3, 7e2, 4e2, 1e2,
     7., 4., 1.])


def get_interface_pressures(p, ps):
    """Given 3D pressure on model mid levels (cell centers) and the 2D surface
    pressure, return the 3D pressure on model full levels (cell interfaces).
    If the z-dimension of p is length K, the returned p_full will have a
    z-dimension of length K+1."""
    interface_pressures = np.zeros(
        (p.shape[0], p.shape[1], p.shape[2]+1), dtype=np.float32)
    interface_pressures[:, :, 1:-1] = 0.5*(p[:, :, 1:] + p[:, :, :-1])
    interface_pressures[:, :, 0] = ps[:, :]
    return interface_pressures


state = {
    'air_temperature': DataArray(
        np.ones((1, 1, len(pressure_axis)))*250.,
        dims=('x', 'y', 'mid_levels'),
        attrs={'units': 'degK'}),
}

constant_state = {
    'surface_temperature': DataArray(
        np.ones((1, 1))*274., dims=('x', 'y'), attrs={'units': 'degK'}),
    'surface_air_pressure': DataArray(
        np.ones((1, 1))*1e5, dims=('x', 'y'), attrs={'units': 'Pa'}),
    'air_pressure': DataArray(
        pressure_axis[None, None, :], dims=('x', 'y', 'mid_levels'),
        attrs={'units': 'Pa'}),
    'latitude': DataArray(
        np.zeros((1,)), dims=('y',), attrs={'units': 'degrees_north'}),
}
interface_pressures = get_interface_pressures(
    constant_state['air_pressure'].values,
    constant_state['surface_air_pressure'].values)
interface_sigma = (
    interface_pressures/constant_state['surface_air_pressure'].values[:, :, None])
constant_state['air_pressure_on_interface_levels'] = DataArray(
    interface_pressures, dims=('x', 'y', 'interface_levels'),
    attrs={'units': 'Pa'})
constant_state['sigma_on_interface_levels'] = DataArray(
    interface_sigma, dims=('x', 'y', 'interface_levels'),
    attrs={'units': ''})

state.update(constant_state)


def plot_function(fig, state):
    ax = fig.add_subplot(1, 1, 1)
    ax.plot(
        state['air_temperature'].values.flatten(),
        state['air_pressure'].values.flatten(), '-o')
    ax.axes.invert_yaxis()
    ax.set_yscale('log')
    ax.set_ylim(1e5, 100.)


monitor = PlotFunctionMonitor(plot_function)
diagnostic = Frierson06LongwaveOpticalDepth()
radiation = GrayLongwaveRadiation()
time_stepper = AdamsBashforth([radiation])
timestep = timedelta(hours=4)

for i in range(6*7*4*10):
    print(i)
    state.update(diagnostic(state))
    diagnostics, new_state = time_stepper.__call__(state, timestep)
    state.update(diagnostics)
    new_state.update(constant_state)
    if i % 5 == 0:
        monitor.store(state)
    state = new_state
