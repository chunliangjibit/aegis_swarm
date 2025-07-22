# Aegis Swarm 2.0 - Apollo Replayer
# This script reads a detailed simulation log (.json) and visualizes it as an animation using Pygame.
# It is launched as a separate process by the Athena Console (main_window.py).

import pygame
import json
import sys
import os

# --- Helper function to find a font ---
def find_font(preferred_fonts, fallback_size=20):
    for font_name in preferred_fonts:
        if pygame.font.match_font(font_name):
            return pygame.font.SysFont(font_name, fallback_size)
    return pygame.font.SysFont(None, fallback_size + 4) # Default fallback

class Replayer:
    def __init__(self, replay_filepath):
        if not os.path.exists(replay_filepath):
            print(f"Error: Replay file not found at '{replay_filepath}'")
            sys.exit(1)

        print(f"Loading replay data from {replay_filepath}...")
        with open(replay_filepath, 'r') as f:
            self.log_data = json.load(f)

        self.metadata = self.log_data.get("metadata", {})
        self.timestamps = self.log_data.get("timestamps", [])
        
        if not self.timestamps:
            print("Error: Replay file contains no timestamp data.")
            sys.exit(1)

        # Extract config from the first timestamp's agent data if possible (for colors etc)
        # This is a bit of a hack, a better log would store the config.
        self.config = {
            'SCREEN_WIDTH': 1600, 'SCREEN_HEIGHT': 900, 'FPS': 60,
            'BG_COLOR': (10, 10, 20), 'INFO_FONT_COLOR': (200, 200, 255),
            'BLUE_COLOR': (0, 150, 255), 'RED_COLOR': (255, 50, 50),
            'HEALTH_BAR_GREEN': (0, 255, 0), 'HEALTH_BAR_RED': (255, 0, 0),
            'DRONE_RADIUS': 5
        }

        # --- Pygame Setup ---
        pygame.init()
        self.screen = pygame.display.set_mode((self.config['SCREEN_WIDTH'], self.config['SCREEN_HEIGHT']))
        sim_id = self.metadata.get('simulation_id', 'Replay')
        pygame.display.set_caption(f"Aegis Swarm Replay: {sim_id}")
        self.clock = pygame.time.Clock()
        self.font = find_font(["consolas", "dejavusansmono", "couriernew"], 20)
        self.big_font = find_font(["bahnschrift", "calibri", "segoeui"], 32)
        
        # --- Playback Control ---
        self.current_frame = 0
        self.is_paused = False
        self.play_speed = 1.0 # 1.0 = normal, 2.0 = double speed, 0.5 = half speed

    def run(self):
        """The main loop for the replay window."""
        running = True
        while running:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE:
                        running = False
                    if event.key == pygame.K_SPACE:
                        self.is_paused = not self.is_paused
                    if event.key == pygame.K_RIGHT: # Fast-forward
                        self.play_speed = min(8.0, self.play_speed * 2)
                    if event.key == pygame.K_LEFT: # Slow-motion
                        self.play_speed = max(0.125, self.play_speed / 2)
                    if event.key == pygame.K_r: # Reset speed
                        self.play_speed = 1.0

            # --- Update ---
            if not self.is_paused:
                self.current_frame += 1
                if self.current_frame >= len(self.timestamps):
                    self.current_frame = len(self.timestamps) - 1 # Pause at the end

            # --- Draw ---
            self.draw_frame()
            
            # --- Timing ---
            self.clock.tick(self.config['FPS'] * self.play_speed)

        pygame.quit()

    def draw_frame(self):
        """Draws a single frame based on the log data."""
        self.screen.fill(self.config['BG_COLOR'])
        
        frame_data = self.timestamps[self.current_frame]
        
        # Draw agents
        for agent_state in frame_data["agents"]:
            pos = agent_state["pos"]
            team_id = agent_state["team_id"]
            color = self.config['BLUE_COLOR'] if team_id == 1 else self.config['RED_COLOR']
            
            # Draw body
            pygame.draw.circle(self.screen, color, (int(pos[0]), int(pos[1])), self.config['DRONE_RADIUS'])
            
            # Draw health bar
            health = agent_state["health"]
            max_health = agent_state["max_health"]
            if health < max_health:
                bar_width = self.config['DRONE_RADIUS'] * 2.5
                bar_height = 4
                bar_x = pos[0] - bar_width / 2
                bar_y = pos[1] - self.config['DRONE_RADIUS'] - bar_height - 5
                health_percentage = health / max_health
                pygame.draw.rect(self.screen, self.config['HEALTH_BAR_RED'], (bar_x, bar_y, bar_width, bar_height))
                pygame.draw.rect(self.screen, self.config['HEALTH_BAR_GREEN'], (bar_x, bar_y, bar_width * health_percentage, bar_height))

        # Draw events (like explosions)
        for event in frame_data["events"]:
            if event["type"] == "detonation":
                pos = event["pos"]
                # Simple explosion effect: a rapidly expanding circle
                # We can tie the circle size to the time since the event, but for now a fixed size is ok.
                pygame.draw.circle(self.screen, (255, 165, 0), pos, 30, 2)
        
        # --- Draw UI / HUD ---
        # Top-left info
        time_text = self.font.render(f"Time: {frame_data['time']:.2f}s", True, self.config['INFO_FONT_COLOR'])
        blue_text = self.font.render(f"Blue: {frame_data['blue_count']}", True, self.config['BLUE_COLOR'])
        red_text = self.font.render(f"Red:  {frame_data['red_count']}", True, self.config['RED_COLOR'])
        self.screen.blit(time_text, (20, 20))
        self.screen.blit(blue_text, (20, 45))
        self.screen.blit(red_text, (20, 70))
        
        # Top-right info (strategies)
        blue_strat_text = self.font.render(f"Blue Strategy: {self.metadata.get('blue_strategy', 'N/A')}", True, self.config['INFO_FONT_COLOR'])
        red_strat_text = self.font.render(f"Red Strategy: {self.metadata.get('red_strategy', 'N/A')}", True, self.config['INFO_FONT_COLOR'])
        self.screen.blit(blue_strat_text, (self.config['SCREEN_WIDTH'] - blue_strat_text.get_width() - 20, 20))
        self.screen.blit(red_strat_text, (self.config['SCREEN_WIDTH'] - red_strat_text.get_width() - 20, 45))

        # Bottom-center controls
        speed_text = self.font.render(f"Speed: {self.play_speed}x", True, self.config['INFO_FONT_COLOR'])
        controls_text = self.font.render("[SPACE] Pause | [<- / ->] Speed | [R] Reset Speed", True, self.config['INFO_FONT_COLOR'])
        self.screen.blit(speed_text, (self.config['SCREEN_WIDTH']/2 - speed_text.get_width()/2, self.config['SCREEN_HEIGHT'] - 60))
        self.screen.blit(controls_text, (self.config['SCREEN_WIDTH']/2 - controls_text.get_width()/2, self.config['SCREEN_HEIGHT'] - 35))

        # Paused overlay
        if self.is_paused:
            paused_text = self.big_font.render("PAUSED", True, (255, 255, 255, 150))
            self.screen.blit(paused_text, (self.config['SCREEN_WIDTH']/2 - paused_text.get_width()/2, self.config['SCREEN_HEIGHT']/2 - paused_text.get_height()/2))

        pygame.display.flip()

if __name__ == '__main__':
    # This allows the script to be called from the command line, e.g., "python replay.py replays/sim_1.json"
    if len(sys.argv) > 1:
        replay_file_path = sys.argv[1]
        replayer = Replayer(replay_file_path)
        replayer.run()
    else:
        print("Usage: python replay.py <path_to_replay_file.json>")
        # As a fallback, try to find the latest replay file
        replays_dir = "replays"
        if os.path.exists(replays_dir):
            all_replays = [os.path.join(replays_dir, f) for f in os.listdir(replays_dir) if f.endswith('.json')]
            if all_replays:
                latest_replay = max(all_replays, key=os.path.getmtime)
                print(f"No file specified, attempting to play latest replay: {latest_replay}")
                replayer = Replayer(latest_replay)
                replayer.run()
            else:
                print("No replay files found in 'replays' directory.")
        else:
            print("No 'replays' directory found.")