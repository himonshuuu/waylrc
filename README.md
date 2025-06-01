# Waylrc - A simple lyrics module for waybar

- using lrclib.net api for lyrics
- playerctl for audio metadata


## Installation

```bash
git clone https://github.com/himonshuuu/waylrc
cd waylrc
sudo install -Dm755 waylrc.py /usr/bin/waylrc
```

## Implement in your waybar
```json
// ~/.config/waybar/config.jsonc
"custom/waylrc": {
        "exec": "waylrc",
        "return-type": "json",
        "interval": 0,
        "format": "{}",
        "tooltip": true
}
```
```css
/* ~/.config/waybar/style.css */
#custom-waykey {
    background-color: #4b4b4b;
}
```