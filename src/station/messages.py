"""Sentences shown on the television. No hyphens or dashes."""

TITLE = "Nostalgia TV"
CHOOSE = "Choose what this television plays."
CHOICE_FILES = "USB drive with your files"
CHOICE_PLEX = "Your Plex server"
FILES_PROMPT = "Insert the drive that holds your videos. Then press OK."
NO_VIDEOS = "No video files were found on the drive."
PLEX_PROMPT = "On your phone, open plex.tv/link and enter this code."
PLEX_WAIT = "Waiting for your Plex account."
PLEX_CODE_EXPIRED = "That code expired. Press OK for a new code."
PLEX_NETWORK = "This television cannot reach Plex yet. Check the network cable."
PLEX_BAD_RESPONSE = "Plex did not answer in a way this television understands."
PLEX_NO_SERVER = "No Plex server was found for that account."
PLEX_DOWN = "Your Plex server did not answer."
PICK_SERVER = "Choose the Plex server."
PICK_CLOCK = "Choose your clock."
REMOTE_HELP = "Channel up and channel down move the choice. OK selects it."
LOADING = "Loading your library."
EMPTY_LIBRARY = "That library has no videos yet."

CLOCKS = (
    ("US Eastern", "America/New_York"),
    ("US Central", "America/Chicago"),
    ("US Mountain", "America/Denver"),
    ("US Pacific", "America/Los_Angeles"),
    ("UK", "Europe/London"),
    ("Central Europe", "Europe/Berlin"),
    ("UTC", "UTC"),
)

BUYER_TEXT = (
    TITLE,
    CHOOSE,
    CHOICE_FILES,
    CHOICE_PLEX,
    FILES_PROMPT,
    NO_VIDEOS,
    PLEX_PROMPT,
    PLEX_WAIT,
    PLEX_CODE_EXPIRED,
    PLEX_NETWORK,
    PLEX_BAD_RESPONSE,
    PLEX_NO_SERVER,
    PLEX_DOWN,
    PICK_SERVER,
    PICK_CLOCK,
    REMOTE_HELP,
    LOADING,
    EMPTY_LIBRARY,
) + tuple(label for label, _zone in CLOCKS)
