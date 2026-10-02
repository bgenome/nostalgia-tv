import os
import json
import random
import subprocess
from datetime import datetime

EPOCH = datetime(2020, 1, 1) # Start of our theoretical 24/7 broadcast

def get_video_duration(filepath):
    """Attempt to get video duration using ffprobe. Fallback to 1200s (20 mins)."""
    try:
        cmd = ['ffprobe', '-v', 'error', '-show_entries', 'format=duration', 
               '-of', 'default=noprint_wrappers=1:nokey=1', filepath]
        output = subprocess.check_output(cmd, stderr=subprocess.STDOUT).decode('utf-8').strip()
        return float(output)
    except Exception as e:
        return 1200.0

class BumperManager:
    def __init__(self, directory):
        self.directory = directory
        self.bumpers = []
        self._load_bumpers()
        
    def _load_bumpers(self):
        if not self.directory or not os.path.exists(self.directory):
            return
        for root, _, files in os.walk(self.directory):
            for f in files:
                if f.endswith(('.mp4', '.mkv', '.avi', '.m4v')):
                    self.bumpers.append(os.path.join(root, f))
                    
    def get_random_bumper(self):
        if not self.bumpers:
            return "OFF_AIR"
        return random.choice(self.bumpers)

class ChannelTimeline:
    def __init__(self, directory, is_random=False, seed=42):
        self.directory = directory
        self.is_random = is_random
        self.seed = seed
        self.videos = []
        self.total_duration = 0.0
        self._build_timeline()
        
    def _build_timeline(self):
        if not os.path.exists(self.directory):
            return
            
        files = []
        # Recursive scanning
        for root, _, filenames in os.walk(self.directory):
            for f in filenames:
                if f.endswith(('.mp4', '.mkv', '.avi', '.m4v')):
                    files.append(os.path.join(root, f))
                    
        if self.is_random:
            random.Random(self.seed).shuffle(files)
        else:
            files.sort() # Alphabetical sorting handles Season 1/Episode 1 ordering
            
        cache_path = os.path.join(self.directory, '.duration_cache.json')
        cache = {}
        if os.path.exists(cache_path):
            try:
                with open(cache_path, 'r') as f:
                    cache = json.load(f)
            except:
                pass
                
        for filepath in files:
            if filepath in cache:
                dur = cache[filepath]
            else:
                dur = get_video_duration(filepath)
                cache[filepath] = dur
                
            self.videos.append({
                'file': filepath,
                'duration': dur,
                'start_offset': self.total_duration
            })
            self.total_duration += dur
            
        try:
            if os.access(self.directory, os.W_OK):
                with open(cache_path, 'w') as f:
                    json.dump(cache, f)
        except:
            pass

    def get_current_playing(self, elapsed_seconds):
        """Returns (filepath, seek_time_in_seconds) or None if timeline is exhausted."""
        if not self.videos or self.total_duration == 0:
            return None, 0
            
        # For a scheduled block, we do NOT loop indefinitely unless we want it to.
        # But for 24/7 channels, we DO loop. We'll handle this by returning None
        # if elapsed_seconds exceeds total_duration in scheduled blocks, 
        # or looping in 24/7 channels.
        
        # Let's assume elapsed_seconds is modulo'd by the caller for 24/7 channels,
        # but passed directly for strict time slots.
        if elapsed_seconds >= self.total_duration:
            return None, 0 # Dead air reached!
            
        for vid in self.videos:
            if vid['start_offset'] <= elapsed_seconds < vid['start_offset'] + vid['duration']:
                seek_time = elapsed_seconds - vid['start_offset']
                return vid['file'], seek_time
                
        return None, 0

class Scheduler:
    def __init__(self, config_parser):
        self.config = config_parser
        self.channels = config_parser.get_all_channels()
        self.timelines = {} 
        self.global_config = config_parser.get_global_config()
        self.bumper_manager = BumperManager(self.global_config.get('bumpers_directory', ''))
        
    def _get_timeline(self, directory, is_random):
        key = f"{directory}_{is_random}"
        if key not in self.timelines:
            self.timelines[key] = ChannelTimeline(directory, is_random=is_random)
        return self.timelines[key]
        
    def get_currently_playing(self, channel_num, current_dt=None):
        if current_dt is None:
            current_dt = datetime.now()
            
        channel = self.channels.get(channel_num)
        if not channel:
            return "OFF_AIR", 0
            
        if channel.type == 'guide':
            return "GUIDE", 0
            
        is_random = (channel.type == 'movies')
        
        if channel.schedule:
            # Scheduled Channel Logic
            active_slot = None
            current_time = current_dt.time()
            for slot in channel.schedule:
                start_t = datetime.strptime(slot['start'], "%H:%M").time()
                end_t = datetime.strptime(slot['end'], "%H:%M").time()
                
                if start_t <= current_time <= end_t:
                    active_slot = slot
                    break
                    
            if active_slot:
                # Find how far into the slot we are
                start_dt = datetime.combine(current_dt.date(), datetime.strptime(active_slot['start'], "%H:%M").time())
                time_in_current_slot = (current_dt - start_dt).total_seconds()
                
                timeline = self._get_timeline(active_slot['directory'], is_random)
                filepath, seek = timeline.get_current_playing(time_in_current_slot)
                
                # If timeline is exhausted before slot ends (dead air), play a bumper
                if not filepath:
                    return self.bumper_manager.get_random_bumper(), 0
                return filepath, seek
            else:
                return self.bumper_manager.get_random_bumper(), 0
                
        else:
            # 24/7 Channel Logic (Loops infinitely)
            active_directory = channel.directory
            if not active_directory:
                return "OFF_AIR", 0
                
            timeline = self._get_timeline(active_directory, is_random)
            if timeline.total_duration == 0:
                return "OFF_AIR", 0
                
            elapsed_seconds = (current_dt - EPOCH).total_seconds()
            cycle_position = elapsed_seconds % timeline.total_duration
            return timeline.get_current_playing(cycle_position)
