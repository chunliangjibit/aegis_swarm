# Aegis Swarm 3.2 - Apollo Replayer (Visual ID Edition)
# UPGRADED: The replayer now reads agent role data and renders Scouts and
# Strikers in their distinct, configured colors for clear tactical analysis.

import pygame
import json
import sys
import os
import numpy as np

def find_font(preferred_fonts, fallback_size=16):
    for font_name in preferred_fonts:
        if pygame.font.match_font(font_name):
            return pygame.font.SysFont(font_name, fallback_size)
    return pygame.font.SysFont(None, fallback_size + 2)

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

        # --- [MODIFIED] Configuration now includes distinct role colors ---
        self.config = {
            'SCREEN_WIDTH': 1600, 'SCREEN_HEIGHT': 900, 'FPS': 60,
            'BG_COLOR': (10, 10, 20), 'INFO_FONT_COLOR': (200, 200, 255),
            'SCOUT_BLUE_COLOR': (100, 200, 255),  # Lighter blue for Scouts
            'STRIKER_BLUE_COLOR': (0, 100, 255),    # Deeper blue for Strikers
            'DEFAULT_BLUE_COLOR': (0, 150, 255), # Fallback blue
            'RED_COLOR': (255, 50, 50),
            'HEALTH_BAR_GREEN': (0, 255, 0), 'HEALTH_BAR_RED': (255, 0, 0),
            'DRONE_RADIUS': 5,
            'TASK_OPEN_COLOR': (255, 255, 100), 'TASK_ASSIGNED_COLOR': (100, 100, 100),
            'BUNDLE_OUTLINE_COLOR': (255, 165, 0),
        }

        pygame.init()
        self.screen = pygame.display.set_mode((self.config['SCREEN_WIDTH'], self.config['SCREEN_HEIGHT']))
        sim_id = self.metadata.get('simulation_id', 'Replay')
        pygame.display.set_caption(f"Aegis Swarm 3.2 Replay: {sim_id}")
        self.clock = pygame.time.Clock()
        self.font = find_font(["consolas", "dejavusansmono", "couriernew"], 18)
        self.hud_font = find_font(["calibri", "segoeui", "sans"], 16)
        self.big_font = find_font(["bahnschrift", "calibri", "segoeui"], 32)
        
        self.current_frame = 0
        self.is_paused = False
        self.play_speed = 1.0
        self.mouse_pos = (0, 0)
        self.hovered_task = None

    def run(self):
        running = True
        while running:
            self.mouse_pos = pygame.mouse.get_pos()
            self.hovered_task = None
            
            for event in pygame.event.get():
                if event.type == pygame.QUIT: running = False
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE: running = False
                    if event.key == pygame.K_SPACE: self.is_paused = not self.is_paused
                    if event.key == pygame.K_RIGHT: self.play_speed = min(8.0, self.play_speed * 2)
                    if event.key == pygame.K_LEFT: self.play_speed = max(0.125, self.play_speed / 2)
                    if event.key == pygame.K_r: self.play_speed = 1.0

            if not self.is_paused:
                self.current_frame = min(self.current_frame + 1, len(self.timestamps) - 1)

            self.draw_frame()
            self.clock.tick(self.config['FPS'] * self.play_speed)
        pygame.quit()

    def draw_frame(self):
        self.screen.fill(self.config['BG_COLOR'])
        if self.current_frame >= len(self.timestamps): return
        frame_data = self.timestamps[self.current_frame]
        
        all_tasks = frame_data.get("tasks", [])
        if all_tasks: max_value = max(t.get('value', 1.0) for t in all_tasks) if any(t.get('value', 0) > 0 for t in all_tasks) else 1.0
        for task_state in sorted(all_tasks, key=lambda t: t.get('is_bundle', False)):
            pos = np.array(task_state["pos"])
            color = self.config['TASK_OPEN_COLOR'] if task_state["status"] == 'OPEN' else self.config['TASK_ASSIGNED_COLOR']
            value_ratio = min(task_state.get('value', 1.0) / max_value, 1.0) if max_value > 0 else 0.5
            color = tuple(min(255, int(c * (0.6 + value_ratio * 0.4))) for c in color)
            if np.linalg.norm(pos - self.mouse_pos) < 20: self.hovered_task = task_state
            if task_state.get('is_bundle', False):
                radius = 8 + int(value_ratio * 8)
                pygame.draw.circle(self.screen, self.config['BUNDLE_OUTLINE_COLOR'], pos.astype(int), radius, 2)
            else:
                size = 6 + int(value_ratio * 4)
                pygame.draw.rect(self.screen, color, (int(pos[0]) - size/2, int(pos[1]) - size/2, size, size))

        # --- [MODIFIED] Agent drawing logic now uses role to determine color ---
        for agent_state in frame_data.get("agents", []):
            pos = agent_state["pos"]; team_id = agent_state["team_id"]
            
            # Determine agent color
            if team_id == 1: # Blue Team
                role = agent_state.get("role", "")
                if role == "scouts":
                    color = self.config['SCOUT_BLUE_COLOR']
                elif role == "strikers":
                    color = self.config['STRIKER_BLUE_COLOR']
                else:
                    color = self.config['DEFAULT_BLUE_COLOR'] # Fallback
            else: # Red Team
                color = self.config['RED_COLOR']
            
            pygame.draw.circle(self.screen, color, (int(pos[0]), int(pos[1])), self.config['DRONE_RADIUS'])
            
            # Health bar logic (no changes)
            health = agent_state["health"]; max_health = agent_state["max_health"]
            if health < max_health:
                bar_width = self.config['DRONE_RADIUS'] * 2.5; bar_height = 4
                bar_x = pos[0] - bar_width / 2; bar_y = pos[1] - self.config['DRONE_RADIUS'] - bar_height - 5
                health_percentage = health / max_health
                pygame.draw.rect(self.screen, self.config['HEALTH_BAR_RED'], (bar_x, bar_y, bar_width, bar_height))
                pygame.draw.rect(self.screen, self.config['HEALTH_BAR_GREEN'], (bar_x, bar_y, bar_width * health_percentage, bar_height))

        for event in frame_data.get("events", []):
            if event["type"] == "detonation": pygame.draw.circle(self.screen, (255, 165, 0), event["pos"], 30, 2)
        
        self.draw_hud_info(frame_data)
        if self.is_paused:
            paused_text = self.big_font.render("PAUSED", True, (255, 255, 255, 150))
            self.screen.blit(paused_text, (self.config['SCREEN_WIDTH']/2 - paused_text.get_width()/2, self.config['SCREEN_HEIGHT']/2 - paused_text.get_height()/2))

        pygame.display.flip()

    def draw_hud_info(self, frame_data):
        # This metadata is now inside the main log, not at the timestamp level
        main_meta = self.log_data.get("metadata", {})
        
        time_text = self.font.render(f"Time: {frame_data['time']:.2f}s", True, self.config['INFO_FONT_COLOR'])
        blue_text = self.font.render(f"Blue: {frame_data['blue_count']}", True, self.config['DEFAULT_BLUE_COLOR'])
        red_text = self.font.render(f"Red:  {frame_data['red_count']}", True, self.config['RED_COLOR'])
        self.screen.blit(time_text, (20, 20)); self.screen.blit(blue_text, (20, 45)); self.screen.blit(red_text, (20, 70))
        
        blue_strat_text = self.hud_font.render(f"Blue Strategy: {main_meta.get('blue_strategy', 'N/A')}", True, self.config['INFO_FONT_COLOR'])
        red_strat_text = self.hud_font.render(f"Red Strategy: {main_meta.get('red_strategy', 'N/A')}", True, self.config['INFO_FONT_COLOR'])
        self.screen.blit(blue_strat_text, (self.config['SCREEN_WIDTH'] - blue_strat_text.get_width() - 20, 20))
        self.screen.blit(red_strat_text, (self.config['SCREEN_WIDTH'] - red_strat_text.get_width() - 20, 45))

        speed_text = self.hud_font.render(f"Speed: {self.play_speed}x", True, self.config['INFO_FONT_COLOR'])
        controls_text = self.hud_font.render("[SPACE] Pause | [<- / ->] Speed | [R] Reset Speed", True, self.config['INFO_FONT_COLOR'])
        self.screen.blit(speed_text, (self.config['SCREEN_WIDTH']/2 - speed_text.get_width()/2, self.config['SCREEN_HEIGHT'] - 60))
        self.screen.blit(controls_text, (self.config['SCREEN_WIDTH']/2 - controls_text.get_width()/2, self.config['SCREEN_HEIGHT'] - 35))

        if self.hovered_task:
            task = self.hovered_task
            task_type = "BUNDLE" if task.get('is_bundle') else "SINGLE"
            info_lines = [
                f"Task Info ({task_type})", f"ID: ...{task.get('id', 'N/A')[-6:]}",
                f"Value: {task.get('value', 0.0):.2f}", f"Status: {task.get('status', 'N/A')}"]
            if task.get('is_bundle'): info_lines.append(f"Sub-Tasks: {task.get('sub_task_count', 0)}")
            box_height = len(info_lines) * 20 + 20; box_width = 200
            box_rect = pygame.Rect(self.config['SCREEN_WIDTH'] - box_width - 15, self.config['SCREEN_HEIGHT'] - box_height - 15, box_width, box_height)
            pygame.draw.rect(self.screen, (20, 30, 50, 200), box_rect); pygame.draw.rect(self.screen, (100, 120, 150), box_rect, 1)
            for i, line in enumerate(info_lines):
                self.screen.blit(self.hud_font.render(line, True, self.config['INFO_FONT_COLOR']), (box_rect.x + 10, box_rect.y + 10 + i * 20))

if __name__ == '__main__':
    if len(sys.argv) > 1:
        replay_file_path = sys.argv[1]
    else:
        print("Usage: python replay.py <path_to_replay_file.json>")
        replays_dir = "replays"
        latest_replay = None
        if os.path.exists(replays_dir):
            all_replays = [os.path.join(replays_dir, f) for f in os.listdir(replays_dir) if f.endswith('.json')]
            if all_replays: latest_replay = max(all_replays, key=os.path.getmtime)
        
        if latest_replay:
            print(f"No file specified, attempting to play latest replay: {latest_replay}")
            replay_file_path = latest_replay
        else:
            print("No replay files found. Exiting.")
            sys.exit(1)
            
    replayer = Replayer(replay_file_path)
    replayer.run()