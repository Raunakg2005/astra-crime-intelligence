import math
from PIL import Image, ImageDraw, ImageFilter

def create_karnataka_map(output_path):
    width, height = 900, 900
    img = Image.new("RGBA", (width, height), (7, 11, 22, 255))
    
    # Create canvas for landmass
    land = Image.new("RGBA", (width, height), (0, 0, 0, 0))
    land_draw = ImageDraw.Draw(land)
    
    # Polygon coordinates for Karnataka (scaled 0..1 to image dimensions)
    # Center map neatly with padding
    def p(x, y):
        margin_x, margin_y = 100, 50
        w_eff, h_eff = width - 2*margin_x, height - 2*margin_y
        return (int(margin_x + x * w_eff), int(margin_y + y * h_eff))

    raw_coords = [
        (0.50, 0.05), # Bidar top
        (0.57, 0.12), # Bidar east
        (0.54, 0.20), # Kalaburagi E
        (0.60, 0.25), # Yadgir E
        (0.62, 0.35), # Raichur E
        (0.65, 0.42), # Ballari E
        (0.60, 0.52), # Chitradurga E
        (0.68, 0.70), # Chikkaballapura E
        (0.76, 0.76), # Kolar E
        (0.72, 0.82), # Kolar S
        (0.62, 0.86), # Bengaluru S
        (0.56, 0.88), # Ramanagara
        (0.50, 0.95), # Chamarajanagar S tip
        (0.42, 0.92), # Mysuru S
        (0.32, 0.88), # Kodagu S
        (0.25, 0.85), # Mangaluru / DK coast
        (0.20, 0.74), # Udupi coast
        (0.18, 0.60), # Uttara Kannada coast
        (0.22, 0.48), # Karwar coast
        (0.20, 0.38), # Goa border
        (0.22, 0.28), # Belagavi W
        (0.30, 0.20), # Belagavi N
        (0.36, 0.18), # Vijayapura N
        (0.44, 0.12), # Kalaburagi N
        (0.50, 0.05)  # Back to Bidar
    ]

    poly = [p(x, y) for x, y in raw_coords]
    
    # Draw land polygon with dark tactical shade
    land_draw.polygon(poly, fill=(18, 26, 41, 255), outline=(220, 38, 38, 180), width=3)

    # Internal district border mesh simulation
    districts = [
        # (x, y, radius, intensity)
        (0.62, 0.82, 38, 1.0),  # Bengaluru
        (0.25, 0.32, 32, 0.9),  # Belagavi
        (0.46, 0.88, 24, 0.85), # Mysuru
        (0.25, 0.83, 26, 0.88), # Mangaluru
        (0.52, 0.18, 22, 0.8),  # Kalaburagi
        (0.32, 0.44, 25, 0.82), # Hubballi
        (0.58, 0.42, 22, 0.8),  # Ballari
        (0.44, 0.56, 20, 0.75), # Davanagere
        (0.35, 0.64, 18, 0.75), # Shivamogga
        (0.54, 0.74, 20, 0.7),  # Tumakuru
        (0.42, 0.78, 18, 0.7),  # Hassan
        (0.40, 0.24, 20, 0.7),  # Vijayapura
        (0.50, 0.09, 16, 0.75), # Bidar
        (0.56, 0.32, 18, 0.7),  # Raichur
        (0.46, 0.40, 16, 0.65), # Koppal
        (0.38, 0.44, 16, 0.65), # Gadag
        (0.38, 0.28, 18, 0.7),  # Bagalkote
        (0.22, 0.52, 18, 0.7),  # Uttara Kannada
        (0.22, 0.73, 16, 0.7),  # Udupi
        (0.36, 0.71, 16, 0.65), # Chikkamagaluru
        (0.50, 0.84, 16, 0.65), # Mandya
        (0.56, 0.85, 14, 0.65), # Ramanagara
        (0.48, 0.92, 16, 0.65), # Chamarajanagar
        (0.34, 0.84, 14, 0.65), # Kodagu
        (0.68, 0.78, 16, 0.7),  # Kolar
        (0.64, 0.73, 16, 0.65), # Chikkaballapura
        (0.48, 0.60, 18, 0.7),  # Chitradurga
        (0.36, 0.52, 16, 0.65), # Haveri
        (0.56, 0.25, 16, 0.65), # Yadgir
        (0.50, 0.48, 16, 0.65), # Vijayanagara
        (0.62, 0.76, 14, 0.60), # Bengaluru Rural
    ]

    # Create district inner partition lines
    district_lines = Image.new("RGBA", (width, height), (0, 0, 0, 0))
    dl_draw = ImageDraw.Draw(district_lines)
    
    # Draw interconnecting subtle lines inside land polygon
    pts = [p(x, y) for x, y, _, _ in districts]
    for i in range(len(pts)):
        for j in range(i+1, len(pts)):
            dist = math.hypot(pts[i][0]-pts[j][0], pts[i][1]-pts[j][1])
            if dist < 120:
                dl_draw.line([pts[i], pts[j]], fill=(244, 63, 94, int(40 * (1 - dist/120))), width=1)

    # Composite land and internal lines
    img.paste(land, (0,0), land)
    img.paste(district_lines, (0,0), district_lines)

    # Red Glowing Heatmap Nodes
    glow_layer = Image.new("RGBA", (width, height), (0, 0, 0, 0))
    glow_draw = ImageDraw.Draw(glow_layer)

    for x_rel, y_rel, r, intensity in districts:
        cx, cy = p(x_rel, y_rel)
        # Outer intense glow
        outer_r = int(r * 2.2)
        glow_draw.ellipse([cx - outer_r, cy - outer_r, cx + outer_r, cy + outer_r], fill=(244, 63, 94, int(70 * intensity)))
        # Mid glow
        mid_r = int(r * 1.3)
        glow_draw.ellipse([cx - mid_r, cy - mid_r, cx + mid_r, cy + mid_r], fill=(239, 68, 68, int(150 * intensity)))
        # Inner core
        core_r = max(4, int(r * 0.5))
        glow_draw.ellipse([cx - core_r, cy - core_r, cx + core_r, cy + core_r], fill=(255, 255, 255, 230))

    # Blur glow layer for smooth heatmap bloom
    glow_blurred = glow_layer.filter(ImageFilter.GaussianBlur(radius=8))
    img.paste(glow_blurred, (0, 0), glow_blurred)

    # Re-draw sharp central cores on top
    core_layer = Image.new("RGBA", (width, height), (0, 0, 0, 0))
    core_draw = ImageDraw.Draw(core_layer)
    for x_rel, y_rel, r, intensity in districts:
        cx, cy = p(x_rel, y_rel)
        c_r = max(3, int(r * 0.4))
        core_draw.ellipse([cx - c_r, cy - c_r, cx + c_r, cy + c_r], fill=(255, 200, 200, 240))
        # Rings around key hubs
        if intensity > 0.8:
            ring_r = int(r * 1.5)
            core_draw.ellipse([cx - ring_r, cy - ring_r, cx + ring_r, cy + ring_r], outline=(244, 63, 94, 200), width=2)

    img.paste(core_layer, (0,0), core_layer)

    # Add scanlines overlay across entire map
    scanline = Image.new("RGBA", (width, height), (0, 0, 0, 0))
    s_draw = ImageDraw.Draw(scanline)
    for y_line in range(0, height, 4):
        s_draw.line([(0, y_line), (width, y_line)], fill=(0, 0, 0, 45), width=1)
    img.paste(scanline, (0, 0), scanline)

    img.save(output_path, "PNG")
    print(f"Map generated successfully at {output_path}")

if __name__ == "__main__":
    create_karnataka_map("frontend/public/hero_karnataka_map.png")
