"""Render UI previews with synthetic data, isolated from accounts and bot input."""
from pathlib import Path
import argparse
import os
import sys
import tempfile
import time
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--scale', type=int, default=100)
    parser.add_argument('--output', default=str(ROOT / 'runtime' / 'ui-preview'))
    args = parser.parse_args()
    out = Path(args.output)
    out.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix='grinding-ui-preview-') as runtime:
        os.environ['MTGA_RUNTIME_DIR'] = runtime
        import ui
        from PIL import ImageGrab

        def config_init(self, config_path=None):
            self.config_path = str(Path(runtime) / 'preview.json')
            self.config = self._default_config()
            self.config.update(ui_scale_percent=args.scale, ui_windows_topmost=False)

        patches = [
            patch.object(ui.ConfigManager, '__init__', config_init),
            patch.object(ui.ConfigManager, '_detect_player_log_path', return_value=''),
            patch.object(ui.ConfigManager, 'get_managed_accounts', return_value=[]),
            patch.object(ui.ConfigManager, '_load_managed_accounts_from_dirs', return_value=[]),
            patch.object(ui.ConfigManager, '_save_config', return_value=None),
            patch.object(ui.MTGBotUI, '_ensure_player_log_path_configured', return_value=True),
            patch.object(ui.MTGBotUI, '_ensure_runtime_prerequisites_confirmed', return_value=True),
            patch.object(ui.MTGBotUI, '_setup_stop_hotkey', return_value=None),
            patch.object(ui.MTGBotUI, '_poll_quests_display', return_value=None),
            patch.object(ui.MTGBotUI, '_fallback_current_account', return_value='Preview account'),
            patch.object(ui.MTGBotUI, '_start_bot', side_effect=AssertionError('Preview cannot start bot')),
        ]
        for p in patches:
            p.start()
        app = None
        try:
            app = ui.MTGBotUI()
            errors = []
            app.report_callback_exception = lambda *error: errors.append(error)
            def capture(window, name):
                window.attributes("-topmost", True)
                window.lift()
                for _ in range(5):
                    app.update()
                    time.sleep(.08)
                x,y=window.winfo_rootx(),window.winfo_rooty()
                ImageGrab.grab(bbox=(x,y,x+window.winfo_width(),y+window.winfo_height())).save(out / (name + '.png'))
            app._render_quests_from_status()
            assert app._menu_buttons['start']['enabled']
            assert not app._menu_buttons['stop']['enabled']
            # Exercise keyboard focus without invoking any real action.
            with patch.dict(app._menu_buttons['start'], command=lambda: errors.append('activated')):
                app._focus_menu_action(1)
                app._activate_focused_menu_action()
                assert errors.pop() == 'activated'
            app._menu_buttons['start']['focused'] = False
            app._refresh_canvas_menu_button_state('start')
            capture(app, f'main-{args.scale}')
            app.session_games, app.session_wins = 12, 8
            app._set_running_state(True)
            app._card_canvas.itemconfigure(app._quest_items[0], text='Cast blue or black spells   12 / 20', fill='#63E6BE')
            app._card_canvas.itemconfigure(app._quest_items[1], text='Play lands   8 / 25')
            app._card_canvas.itemconfigure(app._quest_items[2], text='Attack with creatures   5 / 30')
            app._card_canvas.itemconfigure(app._current_acc_item, text='Current: Preview account')
            app._card_canvas.itemconfigure(app._next_acc_item, text='Next: Second account')
            app._refresh_card_layout()
            capture(app, f'active-{args.scale}')
            app._set_running_state(False)
            app._set_startup_loading(True, 'Preparing card data…')
            capture(app, f'loading-{args.scale}')
            footer_top = app._card_canvas.coords(app._main_topmost_panel_item)[1]
            for item in app._quest_items:
                assert app._card_canvas.bbox(item)[3] < footer_top, 'Quest text overlaps footer'
            for name, button in app._menu_buttons.items():
                box = app._card_canvas.bbox(button['text_item'])
                assert box[2] - box[0] <= button['width'] - 10, f'{name} label is clipped'
            assert app.winfo_width() == app._main_window_size()[0]
            app._set_startup_loading(False)
            # Queue changes remain available only while stopped.
            before = app.config_manager.get_game_mode()
            app._toggle_queue_mode()
            assert app.config_manager.get_game_mode() != before
            app.bot_running = True
            app._toggle_queue_mode()
            assert app.config_manager.get_game_mode() != before
            app.bot_running = False
            app._toggle_queue_mode()
            assert app.config_manager.get_game_mode() == before
            # Rotation updates its labels without touching real account storage.
            app._toggle_account_switch()
            assert not app.config_manager.get_account_switch_enabled()
            app._toggle_account_switch()
            assert app.config_manager.get_account_switch_enabled()
            app._open_settings()
            capture(app.settings_window, f'settings-{args.scale}')
            for cls, name, parent in (
                (ui.SwitchAccountWindow, 'accounts', app.settings_window),
                (ui.UISettingsWindow, 'appearance', app),
                (ui.BotBehaviorWindow, 'behavior', app.settings_window),
                (ui.CalibrationWindow, 'calibration', app),
            ):
                child = cls(parent, app.config_manager, spawn_xy=(300, 30))
                capture(child, f'{name}-{args.scale}')
                child.destroy()
            recording = ui.RecordActionsWindow(app.settings_window, spawn_xy=(300, 30))
            capture(recording, f'recording-{args.scale}')
            recording.destroy()
            app.settings_window.destroy()
            app.settings_window = None
            session = ui.CurrentSessionWindow(app, 12, 8, spawn_xy=(300,30))
            capture(session, f'session-{args.scale}')
            session.destroy()
            # Rebuilding at the same scale must recreate image references too.
            app.apply_ui_scale_live()
            app.update()
            assert app._quest_panel_photo is not None
            assert app._card_canvas.itemcget(app._quest_panel, 'image')
            capture(app, f'rebuilt-{args.scale}')
            if errors:
                raise AssertionError(errors)
            print(f'Preview OK: {app.winfo_width()}x{app.winfo_height()}, screenshots in {out}')
        finally:
            if app is not None:
                app.destroy()
            for p in reversed(patches):
                p.stop()

if __name__ == '__main__':
    main()
