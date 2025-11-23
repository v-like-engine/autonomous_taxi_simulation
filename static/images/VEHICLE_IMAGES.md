# Vehicle Images for Traffic Simulation

This document describes the bird's-eye view images needed for vehicles in the traffic simulation.

## Image Requirements

### Cars
- **Size**: Approximately 4.5m x 2.0m (scaled to pixels)
- **View**: Bird's-eye (top-down view)
- **Variations**: Multiple colors (red, blue, green, yellow, black, white, silver, etc.)
- **Format**: PNG with transparency or SVG

### Trucks
- **Size**: Approximately 8.0m x 2.5m (scaled to pixels)
- **View**: Bird's-eye (top-down view)
- **Variations**: Multiple colors
- **Format**: PNG with transparency or SVG

### Taxi (Main Car)
- **Size**: Approximately 4.5m x 2.0m (scaled to pixels)
- **View**: Bird's-eye (top-down view)
- **Style**: Yandex taxi colors (yellow with black markings)
- **Format**: PNG with transparency or SVG

## Placeholder Implementation

Until actual images are provided, the frontend can render vehicles as:

1. **Simple Rectangles**: Colored rectangles with the correct dimensions
2. **SVG Shapes**: SVG car shapes (see below)
3. **Canvas Drawing**: Draw car shapes using Canvas API

## SVG Templates

### Car SVG Template
```svg
<svg width="50" height="30" viewBox="0 0 50 30" xmlns="http://www.w3.org/2000/svg">
  <!-- Car body -->
  <rect x="5" y="5" width="40" height="20" rx="3" fill="{COLOR}" stroke="black" stroke-width="1"/>
  <!-- Windshield -->
  <rect x="15" y="8" width="10" height="6" fill="#87CEEB" opacity="0.6"/>
  <!-- Rear window -->
  <rect x="28" y="8" width="10" height="6" fill="#87CEEB" opacity="0.6"/>
  <!-- Wheels -->
  <circle cx="12" cy="5" r="3" fill="#333"/>
  <circle cx="38" cy="5" r="3" fill="#333"/>
  <circle cx="12" cy="25" r="3" fill="#333"/>
  <circle cx="38" cy="25" r="3" fill="#333"/>
  <!-- Direction indicator (front) -->
  <polygon points="2,15 5,12 5,18" fill="#FFD700"/>
</svg>
```

### Truck SVG Template
```svg
<svg width="80" height="35" viewBox="0 0 80 35" xmlns="http://www.w3.org/2000/svg">
  <!-- Truck body -->
  <rect x="5" y="5" width="70" height="25" rx="3" fill="{COLOR}" stroke="black" stroke-width="1"/>
  <!-- Cab -->
  <rect x="5" y="8" width="15" height="19" fill="{COLOR}" stroke="black" stroke-width="1"/>
  <!-- Windshield -->
  <rect x="6" y="10" width="8" height="8" fill="#87CEEB" opacity="0.6"/>
  <!-- Cargo area lines -->
  <line x1="25" y1="5" x2="25" y2="30" stroke="black" stroke-width="0.5"/>
  <line x1="45" y1="5" x2="45" y2="30" stroke="black" stroke-width="0.5"/>
  <line x1="65" y1="5" x2="65" y2="30" stroke="black" stroke-width="0.5"/>
  <!-- Wheels -->
  <circle cx="15" cy="5" r="3" fill="#333"/>
  <circle cx="15" cy="30" r="3" fill="#333"/>
  <circle cx="60" cy="5" r="3" fill="#333"/>
  <circle cx="60" cy="30" r="3" fill="#333"/>
  <circle cx="70" cy="5" r="3" fill="#333"/>
  <circle cx="70" cy="30" r="3" fill="#333"/>
  <!-- Direction indicator (front) -->
  <polygon points="2,17.5 5,14 5,21" fill="#FFD700"/>
</svg>
```

### Taxi SVG Template
```svg
<svg width="50" height="30" viewBox="0 0 50 30" xmlns="http://www.w3.org/2000/svg">
  <!-- Taxi body (yellow) -->
  <rect x="5" y="5" width="40" height="20" rx="3" fill="#FFD700" stroke="black" stroke-width="1"/>
  <!-- Black stripe -->
  <rect x="5" y="13" width="40" height="4" fill="#000000"/>
  <!-- Windshield -->
  <rect x="15" y="8" width="10" height="6" fill="#87CEEB" opacity="0.6"/>
  <!-- Rear window -->
  <rect x="28" y="8" width="10" height="6" fill="#87CEEB" opacity="0.6"/>
  <!-- Wheels -->
  <circle cx="12" cy="5" r="3" fill="#333"/>
  <circle cx="38" cy="5" r="3" fill="#333"/>
  <circle cx="12" cy="25" r="3" fill="#333"/>
  <circle cx="38" cy="25" r="3" fill="#333"/>
  <!-- Taxi sign on roof -->
  <rect x="20" y="2" width="10" height="3" fill="#FFD700" stroke="black" stroke-width="0.5"/>
  <text x="25" y="4.5" font-size="2" text-anchor="middle" fill="black">TAXI</text>
  <!-- Direction indicator (front) -->
  <polygon points="2,15 5,12 5,18" fill="#FF0000"/>
</svg>
```

## Image Sources

### Free Resources
1. **OpenGameArt.org**: Search for "top-down car" or "bird's eye car"
2. **Kenney.nl**: Free game assets including top-down vehicles
3. **itch.io**: Many free asset packs with top-down vehicles
4. **Flaticon**: Vector icons of cars (top view)

### Custom Creation
- Use vector graphics software (Inkscape, Adobe Illustrator)
- Create simple top-down car shapes
- Export as SVG or PNG with transparency

### Recommended Free Asset Pack
**Kenney's Car Kit**: https://www.kenney.nl/assets/car-kit
- Includes various top-down vehicle sprites
- Free to use (CC0 license)
- Multiple colors and types

## Implementation Notes

The vehicle rendering will use these images with:
- **Position**: (x, y) coordinates from vehicle state
- **Rotation**: Based on vehicle heading
- **Scale**: Proportional to actual vehicle dimensions
- **Color**: Tinted based on vehicle.color property

The frontend (Agent 3) will handle the actual rendering using these images.
