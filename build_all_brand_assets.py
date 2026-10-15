import os
import math
from PIL import Image, ImageDraw, ImageFilter

def create_master_logo(scale=4, shadow=True):
    size = 512 * scale
    cx, cy = size // 2, size // 2

    # Brand colors from advertisement
    CORAL = (250, 123, 98, 255)  # #FA7B62
    TEAL = (46, 186, 168, 255)   # #2EBAA8

    # Directions
    ucx, ucy = 1.0 / math.sqrt(2), -1.0 / math.sqrt(2)
    utx, uty = 1.0 / math.sqrt(2), 1.0 / math.sqrt(2)

    S = 96 * scale
    W = 56 * scale

    def P(i, j):
        return (cx + i * S * ucx + j * S * utx, cy + i * S * ucy + j * S * uty)

    img = Image.new('RGBA', (size, size), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)

    # 1. Base Coral lines
    for j in [-1, 0, 1]:
        h = 1.62 * S if j == 0 else 1.18 * S
        p_mid = P(0, j)
        p1 = (p_mid[0] - h * ucx, p_mid[1] - h * ucy)
        p2 = (p_mid[0] + h * ucx, p_mid[1] + h * ucy)
        draw.line([p1, p2], fill=CORAL, width=W)
        r = W / 2
        draw.ellipse([p1[0]-r, p1[1]-r, p1[0]+r, p1[1]+r], fill=CORAL)
        draw.ellipse([p2[0]-r, p2[1]-r, p2[0]+r, p2[1]+r], fill=CORAL)

    # 2. Teal lines
    for i in [-1, 0, 1]:
        h = 1.62 * S if i == 0 else 1.18 * S
        p_mid = P(i, 0)
        p1 = (p_mid[0] - h * utx, p_mid[1] - h * uty)
        p2 = (p_mid[0] + h * utx, p_mid[1] + h * uty)
        draw.line([p1, p2], fill=TEAL, width=W)
        r = W / 2
        draw.ellipse([p1[0]-r, p1[1]-r, p1[0]+r, p1[1]+r], fill=TEAL)
        draw.ellipse([p2[0]-r, p2[1]-r, p2[0]+r, p2[1]+r], fill=TEAL)

    # 3. Coral over-patches
    for i, j in [(-1, -1), (1, -1), (0, 0), (-1, 1), (1, 1)]:
        if i == 0 and j == 0:
            p_c = P(0, 0)
            seg = 0.58 * S
            p1 = (p_c[0] - seg * ucx, p_c[1] - seg * ucy)
            p2 = (p_c[0] + seg * ucx, p_c[1] + seg * ucy)
            draw.line([p1, p2], fill=CORAL, width=W)
        else:
            h = 1.18 * S
            p_mid = P(0, j)
            sign = 1 if i == 1 else -1
            p_end = (p_mid[0] + sign * h * ucx, p_mid[1] + sign * h * ucy)
            p_inner = (P(i, j)[0] - sign * 0.58 * W * ucx, P(i, j)[1] - sign * 0.58 * W * ucy)
            draw.line([p_inner, p_end], fill=CORAL, width=W)
            r = W / 2
            draw.ellipse([p_end[0]-r, p_end[1]-r, p_end[0]+r, p_end[1]+r], fill=CORAL)

    # Add optional subtle drop shadow
    if shadow:
        shadow_layer = Image.new('RGBA', (size, size), (0, 0, 0, 0))
        # Extract alpha from img
        alpha_mask = img.split()[3]
        shadow_draw = ImageDraw.Draw(shadow_layer)
        shadow_draw.bitmap((0, 6 * scale), alpha_mask, fill=(15, 23, 42, 35))
        shadow_layer = shadow_layer.filter(ImageFilter.GaussianBlur(8 * scale))
        shadow_layer.paste(img, (0, 0), img)
        img = shadow_layer

    return img

def create_svg():
    size = 512
    cx, cy = 256, 256
    CORAL = '#FA7B62'
    TEAL = '#2EBAA8'
    ucx, ucy = 1.0 / math.sqrt(2), -1.0 / math.sqrt(2)
    utx, uty = 1.0 / math.sqrt(2), 1.0 / math.sqrt(2)
    S = 96
    W = 56

    def P(i, j):
        return (cx + i * S * ucx + j * S * utx, cy + i * S * ucy + j * S * uty)

    svg = f'''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {size} {size}" width="{size}" height="{size}">
  <defs>
    <filter id="shadow" x="-20%" y="-20%" width="140%" height="140%">
      <feDropShadow dx="0" dy="6" stdDeviation="8" flood-color="#0f172a" flood-opacity="0.14" />
    </filter>
  </defs>
  <g filter="url(#shadow)">
'''

    # 1. Base Coral lines
    for j in [-1, 0, 1]:
        h = 1.62 * S if j == 0 else 1.18 * S
        p_mid = P(0, j)
        p1 = (p_mid[0] - h * ucx, p_mid[1] - h * ucy)
        p2 = (p_mid[0] + h * ucx, p_mid[1] + h * ucy)
        svg += f'    <line x1="{p1[0]:.2f}" y1="{p1[1]:.2f}" x2="{p2[0]:.2f}" y2="{p2[1]:.2f}" stroke="{CORAL}" stroke-width="{W}" stroke-linecap="round" />\n'

    # 2. Teal lines
    for i in [-1, 0, 1]:
        h = 1.62 * S if i == 0 else 1.18 * S
        p_mid = P(i, 0)
        p1 = (p_mid[0] - h * utx, p_mid[1] - h * uty)
        p2 = (p_mid[0] + h * utx, p_mid[1] + h * uty)
        svg += f'    <line x1="{p1[0]:.2f}" y1="{p1[1]:.2f}" x2="{p2[0]:.2f}" y2="{p2[1]:.2f}" stroke="{TEAL}" stroke-width="{W}" stroke-linecap="round" />\n'

    # 3. Coral over-patches
    for i, j in [(-1, -1), (1, -1), (0, 0), (-1, 1), (1, 1)]:
        if i == 0 and j == 0:
            p_c = P(0, 0)
            seg = 0.58 * S
            p1 = (p_c[0] - seg * ucx, p_c[1] - seg * ucy)
            p2 = (p_c[0] + seg * ucx, p_c[1] + seg * ucy)
            svg += f'    <line x1="{p1[0]:.2f}" y1="{p1[1]:.2f}" x2="{p2[0]:.2f}" y2="{p2[1]:.2f}" stroke="{CORAL}" stroke-width="{W}" stroke-linecap="butt" />\n'
        else:
            h = 1.18 * S
            p_mid = P(0, j)
            sign = 1 if i == 1 else -1
            p_end = (p_mid[0] + sign * h * ucx, p_mid[1] + sign * h * ucy)
            p_inner = (P(i, j)[0] - sign * 0.58 * W * ucx, P(i, j)[1] - sign * 0.58 * W * ucy)
            svg += f'    <line x1="{p_inner[0]:.2f}" y1="{p_inner[1]:.2f}" x2="{p_end[0]:.2f}" y2="{p_end[1]:.2f}" stroke="{CORAL}" stroke-width="{W}" stroke-linecap="round" />\n'

    svg += '''  </g>
</svg>'''
    return svg

def main():
    print("Generating Master Brand Assets...")
    svg_data = create_svg()
    
    # Save SVG to frontend/public
    with open('frontend/public/icon.svg', 'w') as f:
        f.write(svg_data)
    print("Saved frontend/public/icon.svg")

    # Render high-resolution master PNG (2048x2048)
    master_rgba = create_master_logo(scale=4, shadow=True)
    icon_512 = master_rgba.resize((512, 512), Image.Resampling.LANCZOS)
    icon_512.save('frontend/public/icon.png', 'PNG')
    print("Saved frontend/public/icon.png (512x512 transparent)")

    # Save favicon files
    fav_16 = icon_512.resize((16, 16), Image.Resampling.LANCZOS)
    fav_32 = icon_512.resize((32, 32), Image.Resampling.LANCZOS)
    fav_48 = icon_512.resize((48, 48), Image.Resampling.LANCZOS)
    
    fav_32.save('frontend/public/favicon-32x32.png', 'PNG')
    fav_16.save('frontend/public/favicon-16x16.png', 'PNG')
    icon_512.save('frontend/public/favicon.ico', format='ICO', sizes=[(16, 16), (32, 32), (48, 48)])
    print("Saved favicons (ICO and PNG)")

    # 1. iOS AppIcon: 1024x1024 opaque white background
    print("Generating iOS 1024x1024 AppIcon...")
    ios_icon = Image.new('RGBA', (1024, 1024), (255, 255, 255, 255))
    # Place logo scaled to ~740x740 in center
    logo_740 = icon_512.resize((740, 740), Image.Resampling.LANCZOS)
    ios_icon.paste(logo_740, ((1024 - 740) // 2, (1024 - 740) // 2), logo_740)
    # Convert to RGB (iOS requires no alpha channel in AppIcon-512@2x.png)
    ios_icon_rgb = ios_icon.convert('RGB')
    ios_path = 'frontend/ios/App/App/Assets.xcassets/AppIcon.appiconset/AppIcon-512@2x.png'
    ios_icon_rgb.save(ios_path, 'PNG')
    print(f"Saved iOS AppIcon: {ios_path}")

    # Apple touch icon for web
    apple_touch = ios_icon.resize((180, 180), Image.Resampling.LANCZOS).convert('RGB')
    apple_touch.save('frontend/public/apple-touch-icon.png', 'PNG')

    # Copy to iOS public dir
    os.makedirs('frontend/ios/App/App/public', exist_ok=True)
    with open('frontend/ios/App/App/public/icon.svg', 'w') as f:
        f.write(svg_data)
    icon_512.save('frontend/ios/App/App/public/icon.png', 'PNG')

    # 2. Android Mipmap Icons
    print("Generating Android mipmaps...")
    # Update ic_launcher_background.xml to white
    bg_xml_path = 'frontend/android/app/src/main/res/values/ic_launcher_background.xml'
    with open(bg_xml_path, 'w') as f:
        f.write('''<?xml version="1.0" encoding="utf-8"?>
<resources>
    <color name="ic_launcher_background">#ffffff</color>
</resources>
''')

    densities = {
        'mipmap-mdpi': 48,
        'mipmap-hdpi': 72,
        'mipmap-xhdpi': 96,
        'mipmap-xxhdpi': 144,
        'mipmap-xxxhdpi': 192,
    }

    for folder, dim in densities.items():
        dir_path = os.path.join('frontend/android/app/src/main/res', folder)
        os.makedirs(dir_path, exist_ok=True)

        # A. ic_launcher.png (White background with centered woven logo)
        launcher_img = Image.new('RGBA', (dim, dim), (255, 255, 255, 255))
        # Inner logo size (~72% of canvas)
        inner_dim = int(dim * 0.72)
        inner_logo = icon_512.resize((inner_dim, inner_dim), Image.Resampling.LANCZOS)
        offset = (dim - inner_dim) // 2
        launcher_img.paste(inner_logo, (offset, offset), inner_logo)
        launcher_img.save(os.path.join(dir_path, 'ic_launcher.png'), 'PNG')

        # B. ic_launcher_round.png (Circular white badge with centered woven logo)
        round_img = Image.new('RGBA', (dim, dim), (0, 0, 0, 0))
        round_draw = ImageDraw.Draw(round_img)
        round_draw.ellipse([0, 0, dim - 1, dim - 1], fill=(255, 255, 255, 255))
        round_img.paste(inner_logo, (offset, offset), inner_logo)
        round_img.save(os.path.join(dir_path, 'ic_launcher_round.png'), 'PNG')

        # C. ic_launcher_foreground.png (Adaptive foreground: transparent canvas with centered logo)
        fg_img = Image.new('RGBA', (dim, dim), (0, 0, 0, 0))
        fg_img.paste(inner_logo, (offset, offset), inner_logo)
        fg_img.save(os.path.join(dir_path, 'ic_launcher_foreground.png'), 'PNG')

    # Copy to Android public assets
    os.makedirs('frontend/android/app/src/main/assets/public', exist_ok=True)
    with open('frontend/android/app/src/main/assets/public/icon.svg', 'w') as f:
        f.write(svg_data)
    icon_512.save('frontend/android/app/src/main/assets/public/icon.png', 'PNG')

    print("All Brand Assets successfully generated!")

if __name__ == '__main__':
    main()
