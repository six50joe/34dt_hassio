"""Support for controlling GPIO pins of a Raspberry Pi."""
import logging

from .gpiozerojt import LED, Button
from .gpiozerojt.pins.pigpio import PiGPIOFactory

_LOGGER = logging.getLogger(__name__)

CONF_BOUNCETIME = "bouncetime"
CONF_INVERT_LOGIC = "invert_logic"
CONF_PULL_MODE = "pull_mode"

DEFAULT_BOUNCETIME = 50
DEFAULT_INVERT_LOGIC = False
DEFAULT_PULL_MODE = "UP"

DOMAIN = "remote_rpi_gpio"


def setup(hass, config):
    """Set up the Raspberry Pi Remote GPIO component."""
    return True


def setup_output(address, port, invert_logic):
    """Set up a GPIO as output."""

    try:
        return LED(port, active_high=invert_logic, pin_factory=PiGPIOFactory(address))
    except (ValueError, IndexError, KeyError):
        return None


def setup_input(address, port, pull_mode, bouncetime):
    """Set up a GPIO as input."""

    if pull_mode == "UP":
        pull_gpio_up = True
    elif pull_mode == "DOWN":
        pull_gpio_up = False

    _LOGGER.debug(F"BEFORE BUTTON ")
    try:
        button = gpiozerojt.Button(
            port,
            pull_up=pull_gpio_up,
            bounce_time=bouncetime,
            pin_factory=PiGPIOFactory(address),
        )
        _LOGGER.debug(F"BUTTON={str(button)}")
        return button
    except (ValueError, IndexError, KeyError, OSError) as err:
        _LOGGER.debug(F"EXCEPTION: {err}")
        return None


def write_output(switch, value):
    """Write a value to a GPIO."""
    if value == 1:
        switch.on()
    if value == 0:
        switch.off()


def read_input(button):
    """Read a value from a GPIO."""
    if button is not None:
       _LOGGER.debug(F"BUTTON FOUND: {button}")
       return button.is_pressed
    else:
       _LOGGER.debug("NO BUTTON!!")
       return False
        
