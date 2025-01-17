"""
* PLANAR TEMPLATES
"""
# Standard Library Imports
from typing import Optional
from functools import cached_property

# Third Party Imports
from photoshop.api.application import ArtLayer

# Local Imports
from src.templates._core import StarterTemplate
import src.text_layers as text_classes
from src.enums.layers import LAYERS
from src.layouts import CardLayout
from src.settings import cfg
import src.helpers as psd


class PlanarTemplate (StarterTemplate):
    """
    * Planar template for Planar and Phenomenon cards introduced in the Planechase block.
    """

    def __init__(self, layout: CardLayout):
        cfg.exit_early = True
        super().__init__(layout)

    @cached_property
    def text_layer_static_ability(self) -> ArtLayer:
        return psd.getLayer(LAYERS.STATIC_ABILITY, self.text_group)

    @cached_property
    def text_layer_chaos_ability(self) -> ArtLayer:
        return psd.getLayer(LAYERS.CHAOS_ABILITY, self.text_group)

    def basic_text_layers(self):

        # Add text layers
        self.text.extend([
            text_classes.TextField(
                layer = self.text_layer_name,
                contents = self.layout.name
            ),
            text_classes.ScaledTextField(
                layer = self.text_layer_type,
                contents = self.layout.type_line,
                reference = self.expansion_symbol_layer
            )
        ])

    def rules_text_and_pt_layers(self):

        # Phenomenon card?
        if self.layout.type_line == LAYERS.PHENOMENON:

            # Insert oracle text into static ability layer and disable chaos ability & layer mask on textbox
            self.text.append(
                text_classes.FormattedTextField(
                    layer = self.text_layer_static_ability,
                    contents = self.layout.oracle_text
                )
            )
            psd.enable_mask(psd.getLayerSet(LAYERS.TEXTBOX))
            psd.getLayer(LAYERS.CHAOS_SYMBOL, self.text_group).visible = False
            self.text_layer_chaos_ability.visible = False

        else:

            # Split oracle text on last line break, insert everything before into static, the rest into chaos
            linebreak_index = self.layout.oracle_text.rindex("\n")
            self.text.extend([
                text_classes.FormattedTextField(
                    layer = self.text_layer_static_ability,
                    contents = self.layout.oracle_text[0:linebreak_index]
                ),
                text_classes.FormattedTextField(
                    layer = self.text_layer_chaos_ability,
                    contents = self.layout.oracle_text[linebreak_index+1:]
                ),
            ])

    def paste_scryfall_scan(
        self, reference_layer: Optional[ArtLayer] = None, rotate: bool = False, visible: bool = False
    ) -> Optional[ArtLayer]:
        # Rotate the scan
        return super().paste_scryfall_scan(reference_layer, True, visible)
