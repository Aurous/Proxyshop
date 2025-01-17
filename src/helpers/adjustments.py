# Standard Library
from typing import Union

# Third Party
from photoshop.api import DialogModes, ActionList, ActionDescriptor, ActionReference, SolidColor
from photoshop.api._artlayer import ArtLayer
from photoshop.api._layerSet import LayerSet

# Local Imports
from src.constants import con
from src.helpers.colors import get_color, apply_color, add_color_to_gradient, rgb_black

# QOL Definitions
app = con.app
sID = app.stringIDToTypeID
cID = app.charIDToTypeID
NO_DIALOG = DialogModes.DisplayNoDialogs


def create_vibrant_saturation(vibrancy: int, saturation: int) -> None:
    """
    Experimental scoot action to add vibrancy and saturation.
    @param vibrancy: Vibrancy level integer
    @param saturation: Saturation level integer
    """
    # dialogMode (Have dialog popup?)
    desc232 = ActionDescriptor()
    desc232.putInteger(sID("vibrance"), vibrancy)
    desc232.putInteger(sID("saturation"), saturation)
    app.executeAction(sID("vibrance"), desc232, NO_DIALOG)


def create_color_layer(
    color: SolidColor,
    layer: Union[ArtLayer, LayerSet, None] = None,
    clipped: bool = True,
) -> ArtLayer:
    """
    Create a solid color adjustment layer.
    @param color: Color to use for the layer.
    @param layer: Layer to make active before creation.
    @param clipped: Whether to apply as a clipping mask to the nearest layer.
    @return: The new solid color adjustment layer.
    """
    if layer:
        app.activeDocument.activeLayer = layer
    desc1 = ActionDescriptor()
    ref1 = ActionReference()
    desc2 = ActionDescriptor()
    desc3 = ActionDescriptor()
    ref1.putClass(sID("contentLayer"))
    desc1.putReference(sID("target"), ref1)
    desc2.putBoolean(sID("group"), clipped)
    desc2.putEnumerated(sID("color"), sID("color"), sID("blue"))
    apply_color(desc3, color)
    desc2.putObject(sID("type"), sID("solidColorLayer"), desc3)
    desc1.putObject(sID("using"), sID("contentLayer"), desc2)
    app.executeAction(sID("make"), desc1, NO_DIALOG)
    return app.activeDocument.activeLayer


def create_gradient_layer(
    colors: list[dict],
    layer: Union[None, ArtLayer, LayerSet] = None,
    mask: bool = True
) -> ArtLayer:
    """
    Create a gradient adjustment layer.
    @param colors: List of gradient color dicts.
    @param layer: ArtLayer or LayerSet to make active.
    @param mask: Whether to apply as a clipping mask to the nearest layer.
    @return: The new gradient adjustment layer.
    """
    if layer:
        app.activeDocument.activeLayer = layer
    desc1 = ActionDescriptor()
    ref1 = ActionReference()
    desc2 = ActionDescriptor()
    desc3 = ActionDescriptor()
    desc4 = ActionDescriptor()
    color_list = ActionList()
    list2 = ActionList()
    desc9 = ActionDescriptor()
    desc10 = ActionDescriptor()
    ref1.putClass(sID("contentLayer"))
    desc1.putReference(sID("target"),  ref1)
    desc2.putBoolean(sID("group"), mask)
    desc3.putEnumerated(
        sID("gradientsInterpolationMethod"),
        sID("gradientInterpolationMethodType"),
        sID("perceptual")
    )
    desc3.putEnumerated(sID("type"), sID("gradientType"), sID("linear"))
    desc4.putEnumerated(sID("gradientForm"), sID("gradientForm"), sID("customStops"))
    desc4.putDouble(sID("interfaceIconFrameDimmed"),  4096)
    for c in colors:
        add_color_to_gradient(
            color_list,
            get_color(c.get('color', rgb_black())),
            int(c.get('location', 0)),
            int(c.get('midpoint', 50))
        )
    desc4.putList(sID("colors"),  color_list)
    desc9.putUnitDouble(sID("opacity"), sID("percentUnit"),  100)
    desc9.putInteger(sID("location"),  0)
    desc9.putInteger(sID("midpoint"),  50)
    list2.putObject(sID("transferSpec"),  desc9)
    desc10.putUnitDouble(sID("opacity"), sID("percentUnit"),  100)
    desc10.putInteger(sID("location"),  4096)
    desc10.putInteger(sID("midpoint"),  50)
    list2.putObject(sID("transferSpec"),  desc10)
    desc4.putList(sID("transparency"),  list2)
    desc3.putObject(sID("gradient"), sID("gradientClassEvent"),  desc4)
    desc2.putObject(sID("type"), sID("gradientLayer"),  desc3)
    desc1.putObject(sID("using"), sID("contentLayer"),  desc2)
    app.executeAction(sID("make"), desc1,  NO_DIALOG)
    return app.activeDocument.activeLayer
