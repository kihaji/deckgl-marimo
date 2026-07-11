/**
 * Click/hover pick-event readback: JS -> Python.
 */

/** Shape a deck.gl picking info object into the payload Python receives. */
export function pickPayload(info) {
  return {
    object: info.object ?? null,
    coordinate: info.coordinate,
    layer_id: info.layer ? info.layer.id : null,
    index: info.index,
  };
}

/**
 * Attach onClick/onHover handlers to the overlay that push pick events to
 * the model.
 *
 * Gate on info.picked (deck.gl's canonical "something was picked" flag) so
 * binary-packed layers emit events too — they don't populate info.object.
 */
export function attachPickHandlers(overlay, model) {
  overlay.setProps({
    ...overlay.props,
    onClick: (info) => {
      if (info && info.picked) {
        model.set("click_info", pickPayload(info));
        model.save_changes();
      }
    },
    onHover: (info) => {
      if (info && info.picked) {
        model.set("hover_info", pickPayload(info));
        model.save_changes();
      }
    },
  });
}
