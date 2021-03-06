from climt import (
    mass_to_volume_mixing_ratio,
    get_interface_values)

from sympl import DataArray
import numpy as np
import pytest


def test_mol_weight_not_passed():

    with pytest.raises(ValueError) as excinfo:
        mass_to_volume_mixing_ratio(None)

    assert 'molecular weight' in str(excinfo.value)


def test_for_365ppm():

    mass_mixing_ratio_co2 = 605e-6
    molecular_weight_co2 = 48

    expected_vol_mixing_ratio = 365.0670833333333e-6

    co2 = DataArray(
        mass_mixing_ratio_co2*np.ones((1, 1, 1)),
        dims=['longitude', 'latitude', 'mid_levels'],
        attrs=dict(units='g/g'))

    vol_mixing_ratio = mass_to_volume_mixing_ratio(
        co2, molecular_weight=molecular_weight_co2)

    assert np.all(np.isclose(
        vol_mixing_ratio.values, expected_vol_mixing_ratio))

    assert vol_mixing_ratio.dims == co2.dims


def test_for_g_per_kg():

    mass_mixing_ratio_co2 = 605e-3
    molecular_weight_co2 = 48

    expected_vol_mixing_ratio = 365.0670833333333e-6

    co2 = DataArray(
        mass_mixing_ratio_co2*np.ones((1, 1, 1)),
        dims=['longitude', 'latitude', 'mid_levels'],
        attrs=dict(units='g/kg'))

    vol_mixing_ratio = mass_to_volume_mixing_ratio(
        co2, molecular_weight=molecular_weight_co2)

    assert np.all(np.isclose(
        vol_mixing_ratio.values, expected_vol_mixing_ratio))


def test_interface_levels():

    mid_level_values = np.ones((1, 1, 10))
    surface_value = np.ones((1, 1, 1))

    pressure_mid_level = np.linspace(0.995, 0.001, 10)[None, None, :]
    surface_pressure = 1.

    pressure_interface_level = np.zeros((1, 1, 11))

    pressure_interface_level[:, :, 1:-1] = (
        pressure_mid_level[:, :, 1::] + pressure_mid_level[:, :, :-1])/2.

    pressure_interface_level[:, :, 0] = surface_pressure
    pressure_interface_level[:, :, -1] = 0.0005

    interface_values = get_interface_values(
        mid_level_values, surface_value,
        pressure_mid_level, pressure_interface_level)

    assert np.all(interface_values == np.ones((1, 1, 11)))


if __name__ == '__main__':
    pytest.main([__file__])
