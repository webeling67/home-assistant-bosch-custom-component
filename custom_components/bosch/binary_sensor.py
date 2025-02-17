"""Support for Bosch Thermostat Binary Sensor."""
import logging

from homeassistant.helpers.dispatcher import async_dispatcher_send

from homeassistant.components.binary_sensor import (
    BinarySensorEntity,
)

from bosch_thermostat_client.const import BINARY, ON

from .const import (
    DOMAIN,
    BINARY_SENSOR,
    SIGNAL_BINARY_SENSOR_UPDATE_BOSCH,
    UUID,
    SIGNAL_BOSCH,
    GATEWAY,
)

from .bosch_entity import BoschEntity

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(hass, config_entry, async_add_entities):
    """Set up the Bosch Thermostat from a config entry."""
    uuid = config_entry.data[UUID]
    data = hass.data[DOMAIN][uuid]
    enabled_sensors = config_entry.data.get(BINARY_SENSOR, [])
    data[BINARY_SENSOR] = []

    for bosch_sensor in data[GATEWAY].sensors:
        if bosch_sensor.kind == BINARY:
            data[BINARY_SENSOR].append(
                BoschBinarySensor(
                    hass=hass,
                    uuid=uuid,
                    bosch_object=bosch_sensor,
                    gateway=data[GATEWAY],
                    name=bosch_sensor.name,
                    attr_uri=bosch_sensor.attr_id,
                    is_enabled=bosch_sensor.attr_id in enabled_sensors,
                )
            )

    async_add_entities(data[BINARY_SENSOR])
    async_dispatcher_send(hass, SIGNAL_BOSCH)
    return True


class BoschBinarySensor(BoschEntity, BinarySensorEntity):
    """Bosch binary sensor class."""

    signal = SIGNAL_BINARY_SENSOR_UPDATE_BOSCH
    _domain_name = "Sensors"

    def __init__(
        self,
        hass,
        uuid,
        bosch_object,
        gateway,
        name,
        attr_uri,
        is_enabled=False,
    ):
        """Initialize the sensor."""
        super().__init__(
            hass=hass, uuid=uuid, bosch_object=bosch_object, gateway=gateway
        )

        self._name = name
        self._attr_uri = attr_uri
        self._state = None
        self._update_init = True

        self._unique_id = self._domain_name + self._name + self._uuid
        self._attrs = {}
        self._is_enabled = is_enabled

    async def async_added_to_hass(self):
        """Register callbacks."""
        self.hass.helpers.dispatcher.async_dispatcher_connect(
            self.signal, self.async_update
        )

    @property
    def _domain_identifier(self):
        return {(DOMAIN, self._domain_name + self._uuid)}

    @property
    def device_state_attributes(self):
        """Return the state attributes of the sensor."""
        return self._attrs

    @property
    def device_name(self):
        """Return name displayed in device_info"""
        return "Bosch sensors"

    @property
    def entity_registry_enabled_default(self):
        """Return if the entity should be enabled when first added to the entity registry."""
        return self._is_enabled

    async def async_update(self):
        """Update state of device."""
        _LOGGER.debug("Update of binary sensor %s called.", self.unique_id)
        self._attr_is_on = True if self._bosch_object.state.lower() == ON else False

        self._attrs["stateExtra"] = self._bosch_object.state_message
        self.attrs_write(data=self._bosch_object.get_property(self._attr_uri))

    def attrs_write(self, data):
        self._attrs = data
        if self._update_init:
            self._update_init = False
            self.async_schedule_update_ha_state()
