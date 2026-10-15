import os
import sys
import math
import subprocess
from PIL import Image, ImageDraw, ImageFont, ImageFilter

WIDTH = 1920
HEIGHT = 1080
FPS = 30
TOTAL_FRAMES = 450  # 15.0 seconds

BG_PATH = '/home/ubuntu/.gemini/antigravity-cli/brain/db496a9b-b77b-4961-895c-3b5ea4e821b2/community_weave_ad_png_1792055088206.jpg'
ICON_PATH = 'frontend/public/icon.png'
AUDIO_PATH = '/home/ubuntu/community_weave/promo_jingle.wav'
OUTPUT_VIDEO = '/home/ubuntu/community_weave/community_weave_advertisement.mp4'

FONT_BOLD = '/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf'
FONT_REG = '/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf'

def ease_out_cubic(x):
    return 1 - pow(1 - x, 3)

def ease_in_out(x):
    return x * x * (3 - 2 * x)

def clamp(val, min_val, max_val):
    return max(min_val, min(max_val, val))

def main():
    print("Loading base assets...")
    base_bg = Image.open(BG_PATH).convert('RGB')
    orig_w, orig_h = base_bg.size
    
    app_icon = Image.open(ICON_PATH).convert('RGBA')
    
    # Fonts
    f_brand_title = ImageFont.truetype(FONT_BOLD, 32)
    f_brand_sub = ImageFont.truetype(FONT_BOLD, 15)
    f_hero_title = ImageFont.truetype(FONT_BOLD, 42)
    f_hero_sub = ImageFont.truetype(FONT_REG, 24)
    f_card_title = ImageFont.truetype(FONT_BOLD, 22)
    f_card_sub = ImageFont.truetype(FONT_REG, 18)
    f_outro_title = ImageFont.truetype(FONT_BOLD, 58)
    f_outro_tagline = ImageFont.truetype(FONT_REG, 26)
    f_outro_cta = ImageFont.truetype(FONT_BOLD, 26)
    f_outro_url = ImageFont.truetype(FONT_BOLD, 22)

    # Pre-render dark outro background
    outro_base = Image.new('RGB', (WIDTH, HEIGHT), (11, 19, 43))
    outro_draw = ImageDraw.Draw(outro_base, 'RGBA')
    # Add ambient teal radial gradient in the center
    for r in range(400, 0, -10):
        alpha = int(40 * (1.0 - r / 400.0))
        outro_draw.ellipse([WIDTH//2 - r, HEIGHT//2 - r - 60, WIDTH//2 + r, HEIGHT//2 + r - 60], fill=(13, 148, 136, alpha))

    # Setup ffmpeg process
    cmd = [
        'ffmpeg',
        '-y',
        '-f', 'rawvideo',
        '-vcodec', 'rawvideo',
        '-s', f'{WIDTH}x{HEIGHT}',
        '-pix_fmt', 'rgb24',
        '-r', str(FPS),
        '-i', '-',
        '-i', AUDIO_PATH,
        '-c:v', 'libx264',
        '-pix_fmt', 'yuv420p',
        '-preset', 'fast',
        '-crf', '18',
        '-c:a', 'aac',
        '-b:a', '192k',
        '-shortest',
        OUTPUT_VIDEO
    ]

    print(f"Starting ffmpeg rendering for {TOTAL_FRAMES} frames...")
    proc = subprocess.Popen(cmd, stdin=subprocess.PIPE)

    for frame_idx in range(TOTAL_FRAMES):
        t = frame_idx / float(FPS)
        
        # --- SCENE TIMINGS ---
        # 0.0 to 11.5s: Photo scenes with Ken Burns
        # 11.5 to 15.0s: Outro
        
        if frame_idx < 345:
            # Ken Burns Camera movement
            if frame_idx < 130:
                # Scene 1: Slow gentle zoom
                progress = frame_idx / 130.0
                scale = 1.0 + 0.08 * progress
                cx_rel = 0.50
                cy_rel = 0.50
            elif frame_idx < 255:
                # Scene 2: Pan slightly towards neighbors
                progress = (frame_idx - 130) / 125.0
                scale = 1.08 + 0.08 * progress
                cx_rel = 0.50 + 0.08 * ease_in_out(progress)
                cy_rel = 0.50 - 0.02 * ease_in_out(progress)
            else:
                # Scene 3: Drift towards the smartphone
                progress = (frame_idx - 255) / 90.0
                scale = 1.16 + 0.04 * progress
                cx_rel = 0.58 - 0.12 * ease_in_out(progress)
                cy_rel = 0.48 + 0.02 * ease_in_out(progress)
            
            # Crop and resize base image
            crop_w = orig_w / scale
            crop_h = orig_h / scale
            cx = orig_w * cx_rel
            cy = orig_h * cy_rel
            
            x1 = clamp(int(cx - crop_w / 2), 0, int(orig_w - crop_w))
            y1 = clamp(int(cy - crop_h / 2), 0, int(orig_h - crop_h))
            x2 = x1 + int(crop_w)
            y2 = y1 + int(crop_h)
            
            cropped = base_bg.crop((x1, y1, x2, y2))
            frame_img = cropped.resize((WIDTH, HEIGHT), Image.Resampling.BILINEAR)
            
            # Draw overlay layer
            overlay = Image.new('RGBA', (WIDTH, HEIGHT), (0, 0, 0, 0))
            draw = ImageDraw.Draw(overlay)
            
            # Subtle top & bottom cinematic dark gradients
            draw.rectangle([0, 0, WIDTH, 160], fill=(10, 15, 29, 90))
            draw.rectangle([0, HEIGHT - 240, WIDTH, HEIGHT], fill=(10, 15, 29, 140))
            
            # Top-left persistent Brand Pill
            top_pill_alpha = min(220, int(frame_idx * 15))
            draw.rounded_rectangle([60, 50, 520, 130], radius=22, fill=(15, 23, 42, top_pill_alpha), outline=(45, 212, 191, top_pill_alpha), width=2)
            draw.text((140, 62), 'Community Weave', font=f_brand_title, fill=(255, 255, 255, top_pill_alpha))
            draw.text((142, 98), 'HYPERLOCAL NEIGHBOR SHARING', font=f_brand_sub, fill=(45, 212, 191, top_pill_alpha))
            
            small_icon = app_icon.resize((56, 56), Image.Resampling.LANCZOS)
            overlay.paste(small_icon, (72, 62), small_icon)
            
            # Scene 1 Overlays (Frames 0 to 125)
            if frame_idx < 125:
                # Lower third title card fades in
                card_alpha = int(clamp((frame_idx - 15) / 25.0, 0.0, 1.0) * 235)
                if frame_idx > 105:
                    card_alpha = int(clamp((125 - frame_idx) / 20.0, 0.0, 1.0) * 235)
                
                if card_alpha > 0:
                    draw.rounded_rectangle([60, 870, 1140, 1010], radius=24, fill=(15, 23, 42, card_alpha), outline=(20, 184, 166, card_alpha), width=2)
                    # Accent color stripe
                    draw.rounded_rectangle([60, 870, 72, 1010], radius=4, fill=(20, 184, 166, card_alpha))
                    draw.text((95, 888), 'Bayanihan in the Digital Age', font=f_hero_title, fill=(255, 255, 255, card_alpha))
                    draw.text((97, 946), 'Share More • Spend Less • Connect With Your Neighbors', font=f_hero_sub, fill=(45, 212, 191, card_alpha))
            
            # Scene 2 Overlays: Animated feature cards (Frames 126 to 255)
            elif frame_idx < 255:
                # Card 1: Tools (enters at f=130)
                p1 = clamp((frame_idx - 130) / 20.0, 0.0, 1.0)
                if p1 > 0:
                    slide1 = int((1.0 - ease_out_cubic(p1)) * 400)
                    a1 = int(p1 * 235)
                    x_card = 1150 + slide1
                    draw.rounded_rectangle([x_card, 220, x_card + 700, 310], radius=18, fill=(15, 23, 42, a1), outline=(45, 212, 191, a1), width=2)
                    # Pill tag
                    draw.rounded_rectangle([x_card + 20, 235, x_card + 125, 265], radius=8, fill=(234, 88, 12, a1))
                    draw.text((x_card + 32, 240), 'TOOLS', font=f_brand_sub, fill=(255, 255, 255, a1))
                    draw.text((x_card + 140, 238), 'Need Tools or Gear?', font=f_card_title, fill=(251, 191, 36, a1))
                    draw.text((x_card + 25, 273), 'Borrow drills, ladders & washers nearby for free', font=f_card_sub, fill=(241, 245, 249, a1))

                # Card 2: Food & Harvests (enters at f=165)
                p2 = clamp((frame_idx - 165) / 20.0, 0.0, 1.0)
                if p2 > 0:
                    slide2 = int((1.0 - ease_out_cubic(p2)) * 400)
                    a2 = int(p2 * 235)
                    x_card2 = 1150 + slide2
                    draw.rounded_rectangle([x_card2, 335, x_card2 + 700, 425], radius=18, fill=(15, 23, 42, a2), outline=(249, 115, 22, a2), width=2)
                    # Pill tag
                    draw.rounded_rectangle([x_card2 + 20, 350, x_card2 + 120, 380], radius=8, fill=(16, 185, 129, a2))
                    draw.text((x_card2 + 35, 355), 'FOOD', font=f_brand_sub, fill=(255, 255, 255, a2))
                    draw.text((x_card2 + 135, 353), 'Backyard Harvests', font=f_card_title, fill=(249, 115, 22, a2))
                    draw.text((x_card2 + 25, 388), 'Share calamansi, cacao tablea & plant cuttings', font=f_card_sub, fill=(241, 245, 249, a2))

                # Card 3: Help & Mutual Aid (enters at f=200)
                p3 = clamp((frame_idx - 200) / 20.0, 0.0, 1.0)
                if p3 > 0:
                    slide3 = int((1.0 - ease_out_cubic(p3)) * 400)
                    a3 = int(p3 * 235)
                    x_card3 = 1150 + slide3
                    draw.rounded_rectangle([x_card3, 450, x_card3 + 700, 540], radius=18, fill=(15, 23, 42, a3), outline=(56, 189, 248, a3), width=2)
                    # Pill tag
                    draw.rounded_rectangle([x_card3 + 20, 465, x_card3 + 120, 495], radius=8, fill=(14, 165, 233, a3))
                    draw.text((x_card3 + 37, 470), 'HELP', font=f_brand_sub, fill=(255, 255, 255, a3))
                    draw.text((x_card3 + 135, 468), 'Barangay Mutual Aid', font=f_card_title, fill=(56, 189, 248, a3))
                    draw.text((x_card3 + 25, 503), 'Car jumpstarts, tutoring & elder clinic escorts', font=f_card_sub, fill=(241, 245, 249, a3))

            # Scene 3 Overlays: Live Map & Statistics (Frames 256 to 345)
            else:
                p_map = clamp((frame_idx - 256) / 22.0, 0.0, 1.0)
                if frame_idx > 330:
                    p_map = clamp((345 - frame_idx) / 15.0, 0.0, 1.0)
                a_map = int(p_map * 240)
                
                if a_map > 0:
                    draw.rounded_rectangle([700, 780, 1840, 1010], radius=24, fill=(15, 23, 42, a_map), outline=(45, 212, 191, a_map), width=2)
                    draw.text((740, 805), 'Real-Time Neighborhood Explore Map', font=f_hero_title, fill=(255, 255, 255, a_map))
                    draw.text((742, 862), 'Interactive pins across Caloocan, QC, Manila, Makati, Pasig, Cebu & beyond', font=f_card_sub, fill=(45, 212, 191, a_map))
                    
                    # 3 pill badges
                    badge_y = 915
                    draw.rounded_rectangle([740, badge_y, 970, badge_y + 55], radius=12, fill=(13, 148, 136, a_map))
                    draw.text((765, badge_y + 15), '28 Active Seeds', font=f_card_title, fill=(255, 255, 255, a_map))

                    draw.rounded_rectangle([990, badge_y, 1350, badge_y + 55], radius=12, fill=(30, 41, 59, a_map), outline=(45, 212, 191, a_map), width=1)
                    draw.text((1015, badge_y + 15), 'Metro Manila & Hubs', font=f_card_title, fill=(241, 245, 249, a_map))

                    draw.rounded_rectangle([1370, badge_y, 1680, badge_y + 55], radius=12, fill=(30, 41, 59, a_map), outline=(249, 115, 22, a_map), width=1)
                    draw.text((1395, badge_y + 15), '100% Free Sharing', font=f_card_title, fill=(251, 146, 60, a_map))

            # Composite overlay
            frame_img.paste(overlay, (0, 0), overlay)
            
            # Crossfade into outro if near end of scene 3 (335 to 345)
            if frame_idx >= 335:
                cross = (frame_idx - 335) / 10.0
                frame_img = Image.blend(frame_img, outro_base, cross)

        # --- SCENE 4: BRAND FINALE & OUTRO (Frames 345 to 450) ---
        else:
            frame_img = outro_base.copy()
            overlay = Image.new('RGBA', (WIDTH, HEIGHT), (0, 0, 0, 0))
            draw = ImageDraw.Draw(overlay)
            
            outro_prog = clamp((frame_idx - 345) / 25.0, 0.0, 1.0)
            a_outro = int(outro_prog * 255)
            
            # Big Pulsing App Icon
            pulse = math.sin((frame_idx - 345) * 0.12) * 6
            icon_size = int(170 + pulse)
            large_icon = app_icon.resize((icon_size, icon_size), Image.Resampling.LANCZOS)
            
            icon_x = WIDTH // 2 - icon_size // 2
            icon_y = 190 - int(pulse // 2)
            
            # Aura glow around icon
            draw.ellipse([icon_x - 30, icon_y - 30, icon_x + icon_size + 30, icon_y + icon_size + 30], fill=(45, 212, 191, int(35 * outro_prog)))
            overlay.paste(large_icon, (icon_x, icon_y), large_icon)
            
            # Title
            t_text = 'Community Weave'
            t_box = draw.textbbox((0, 0), t_text, font=f_outro_title)
            t_w = t_box[2] - t_box[0]
            draw.text(((WIDTH - t_w)//2, 420), t_text, font=f_outro_title, fill=(255, 255, 255, a_outro))
            
            # Tagline
            sub_text = 'Share More • Spend Less • Build Community'
            s_box = draw.textbbox((0, 0), sub_text, font=f_outro_tagline)
            s_w = s_box[2] - s_box[0]
            draw.text(((WIDTH - s_w)//2, 495), sub_text, font=f_outro_tagline, fill=(45, 212, 191, a_outro))
            
            # CTA Pill Button
            cta_text = 'START SHARING IN YOUR BARANGAY'
            c_box = draw.textbbox((0, 0), cta_text, font=f_outro_cta)
            c_w = c_box[2] - c_box[0]
            btn_x1 = (WIDTH - c_w)//2 - 40
            btn_y1 = 600
            btn_x2 = (WIDTH + c_w)//2 + 40
            btn_y2 = 680
            draw.rounded_rectangle([btn_x1, btn_y1, btn_x2, btn_y2], radius=28, fill=(13, 148, 136, a_outro), outline=(94, 234, 212, a_outro), width=2)
            draw.text(((WIDTH - c_w)//2, 624), cta_text, font=f_outro_cta, fill=(255, 255, 255, a_outro))
            
            # Platforms & Web Address
            platform_text = 'Available on Web  •  Android APK  •  iOS App'
            p_box = draw.textbbox((0, 0), platform_text, font=f_card_sub)
            draw.text(((WIDTH - (p_box[2] - p_box[0]))//2, 735), platform_text, font=f_card_sub, fill=(203, 213, 225, a_outro))

            url_text = 'https://communityweave.duckdns.org'
            u_box = draw.textbbox((0, 0), url_text, font=f_outro_url)
            draw.text(((WIDTH - (u_box[2] - u_box[0]))//2, 785), url_text, font=f_outro_url, fill=(45, 212, 191, a_outro))
            
            # Fade to black on the final 10 frames
            if frame_idx > 435:
                fade_black = int(((frame_idx - 435) / 15.0) * 255)
                draw.rectangle([0, 0, WIDTH, HEIGHT], fill=(0, 0, 0, fade_black))

            frame_img.paste(overlay, (0, 0), overlay)

        # Write RGB raw bytes to ffmpeg stdin
        proc.stdin.write(frame_img.tobytes())
        
        if (frame_idx + 1) % 45 == 0 or frame_idx == TOTAL_FRAMES - 1:
            print(f"Rendered frame {frame_idx + 1}/{TOTAL_FRAMES} ({(frame_idx + 1)/TOTAL_FRAMES*100:.1f}%)")

    proc.stdin.close()
    proc.wait()
    print("Video generation completed successfully!")
    print(f"Saved to: {OUTPUT_VIDEO}")

if __name__ == '__main__':
    main()
