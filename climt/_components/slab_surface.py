from climt._core.climt_components import ClimtPrognostic
import numpy as np


class SlabSurface(ClimtPrognostic):
    """
    Calculate the surface energy balance.

    This component assumes the surface is a slab of possibly
    varying heat capacity, and calculates the surface temperature.
    """

    _climt_inputs = {
        'downwelling_longwave_flux_in_air': 'W m^-2',
        'downwelling_shortwave_flux_in_air': 'W m^-2',
        'upwelling_longwave_flux_in_air': 'W m^-2',
        'upwelling_shortwave_flux_in_air': 'W m^-2',
        'surface_upward_latent_heat_flux': 'W m^-2',
        'surface_upward_sensible_heat_flux': 'W m^-2',
        'surface_thermal_capacity': 'J kg^-1 degK^-1',
        'depth_slab_surface': 'm',
        'density_surface_material': 'kg m^-3',
        'upward_heat_flux_at_ground_level_in_soil': 'W m^-2',
        'heat_flux_into_sea_water_due_to_sea_ice': 'W m^-2',
        'area_type': 'dimensionless',
        'snow_ice_temperature': 'dimensionless',
        'ocean_mixed_layer_thickness': 'm',
        'soil_thermal_capacity': 'J kg^-1 degK^-1',
        'sea_water_density': 'kg m^-3',
    }

    _climt_tendencies = {
        'surface_temperature': 'degK s^-1',
        # 'sea_surface_temperature': 'degK s^-1',
        # 'soil_surface_temperature': 'degK s^-1',
    }

    _climt_diagnostics = {}

    quantity_descriptions = {
        'surface_thermal_capacity': {
            'dims': ['x', 'y'],
            'units': 'J kg^-1 degK^-1',
            'default_value': 4.1813e3
        },
        'depth_slab_surface': {
            'dims': ['x', 'y'],
            'units': 'm',
            'default_value': 50.
        },
        'density_surface_material': {
            'dims': ['x', 'y'],
            'units': 'kg m^-3',
            'default_value': 1000.
        }
    }
    """
    Quantities used for surface heat capacity calculation.
    """

    def __init__(self,
                 thermal_conductivity_of_ice=2.22,
                 thermal_conductivity_of_snow=0.2,
                 melting_point_of_ice=271.
                 ):
        """
        Initialise slab surface

        Args:

            thermal_conductivity_of_ice (float, optional):
                The thermal conductivity of ice in :math:`W m^{-1} K^{-1}`.

            thermal_conductivity_of_snow (float, optional):
                The thermal conductivity of ice in :math:`W m^{-1} K^{-1}`.

            melting_point_of_ice (float, optional):
                The melting point of ice in :math:`degK`.
        """

        self._K_snow = thermal_conductivity_of_snow
        self._K_ice = thermal_conductivity_of_ice
        self._ice_melt_temp = melting_point_of_ice

    def __call__(self, state):
        """
        Calculate surface temperature.

        Args:
            state (dict):
                The state dictionary

        Returns:
            tendencies (dict), diagnostics(dict):
                * The surface temperature tendency
                * Any diagnostics

        """

        raw_arrays = self.get_numpy_arrays_from_state('_climt_inputs', state)

        net_heat_flux = (raw_arrays['downwelling_shortwave_flux_in_air'][:, :, 0] +
                         raw_arrays['downwelling_longwave_flux_in_air'][:, :, 0] -
                         raw_arrays['upwelling_shortwave_flux_in_air'][:, :, 0] -
                         raw_arrays['upwelling_longwave_flux_in_air'][:, :, 0] -
                         raw_arrays['surface_upward_sensible_heat_flux'] -
                         raw_arrays['surface_upward_latent_heat_flux'])

        # TODO get separate tendencies for sea and land surface
        area_type = raw_arrays['area_type'].astype(str)

        land_mask = np.logical_or(area_type == 'land', area_type == 'land_ice')
        sea_mask = np.logical_or(area_type == 'sea', area_type == 'sea_ice')
        land_ice_mask = area_type == 'land_ice'
        sea_ice_mask = area_type == 'sea_ice'

        net_heat_flux[land_ice_mask] = -raw_arrays['upward_heat_flux_at_ground_level_in_soil'][land_ice_mask]

        net_heat_flux[sea_ice_mask] = raw_arrays['heat_flux_into_sea_water_due_to_sea_ice'][sea_ice_mask]

        raw_arrays['density_surface_material'][sea_mask] = raw_arrays['sea_water_density'][sea_mask]

        raw_arrays['surface_thermal_capacity'][land_mask] = raw_arrays['soil_thermal_capacity'][land_mask]

        raw_arrays['depth_slab_surface'][sea_mask] = raw_arrays['ocean_mixed_layer_thickness'][sea_mask]

        mass_surface_slab = raw_arrays['density_surface_material']*raw_arrays['depth_slab_surface']
        heat_capacity_surface = mass_surface_slab*raw_arrays['surface_thermal_capacity']

        tend_dict = self.create_state_dict_for('_climt_tendencies', state)
        diag_dict = self.create_state_dict_for('_climt_diagnostics', state)

        tend_dict['surface_temperature'].values[:] = net_heat_flux/heat_capacity_surface

        return tend_dict, diag_dict
