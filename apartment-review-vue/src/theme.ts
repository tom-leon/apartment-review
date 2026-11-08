import { definePreset, palette } from "@primevue/themes";
import Aura from "@primevue/themes/aura";

// Vue green, with dark green button text because white on #42b883 is too faint to read.
export default definePreset(Aura, {
  semantic: {
    primary: palette("#42b883"),
    colorScheme: {
      light: {
        primary: {
          contrastColor: "{primary.950}",
          hoverColor: "{primary.400}",
          activeColor: "{primary.300}",
        },
      },
    },
  },
  components: {
    // Slider handle: a tall rounded rectangle instead of Aura's circle.
    slider: {
      handle: {
        width: "14px",
        height: "24px",
        borderRadius: "4px",
        content: { width: "10px", height: "20px", borderRadius: "3px" },
      },
    },
  },
});
