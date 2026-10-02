import yaml
import os

class ChannelConfig:
    def __init__(self, channel_num, data):
        self.channel_num = channel_num
        self.name = data.get('name', f"Channel {channel_num}")
        self.type = data.get('type', 'tv_shows')
        self.directory = data.get('directory', '')
        self.schedule = data.get('schedule', [])

class ConfigParser:
    def __init__(self, config_path):
        self.config_path = config_path
        self.channels = {}
        self.global_config = {}
        
    def load(self):
        if not os.path.exists(self.config_path):
            raise FileNotFoundError(f"Config file not found: {self.config_path}")
            
        with open(self.config_path, 'r') as f:
            data = yaml.safe_load(f)
            
        if not data:
            return
            
        self.global_config = data.get('global', {})
            
        if 'channels' in data:
            for ch_num, ch_data in data['channels'].items():
                self.channels[int(ch_num)] = ChannelConfig(int(ch_num), ch_data)
            
    def get_global_config(self):
        return self.global_config
        
    def get_channel(self, channel_num):
        return self.channels.get(channel_num)
        
    def get_all_channels(self):
        return self.channels
