screen beatTheBeat(audio_path, beatmap_path):
    default BeatTheBeat_displayble = BeatTheBeatDisplayable(audio_path, beatmap_path)

    add BeatTheBeat_displayble

    #pokazanie wyniku i umiejscowienie go w odpowiednim miejscu na ekranie
    text 'Hits: ' + str(BeatTheBeat_displayble.num_hits):
        color '#fff' xpos 50 ypos 50

    #zwraca liczbę trafień i całkowitą liczbę nut
    if BeatTheBeat_displayble.has_ended:
        # use a timer so the player can see the screen before it returns
        timer 2.0 action Return(
            (BeatTheBeat_displayble.num_hits, BeatTheBeat_displayble.num_notes)
            )

init python:

    import os
    import pygame

    class BeatTheBeatDisplayable(renpy.Displayable):

        def __init__(self, audio_path, beatmap_path):
            super(BeatTheBeatDisplayable, self).__init__()

            self.audio_path = audio_path

            self.has_started = False
            self.has_ended = False
            # offset jest konieczny, ponieważ może wystąpić opóźnienie
            # między pierwszym pojawieniem się elementu do wyświetlenia
            # na ekranie a rozpoczęciem odtwarzania muzyki
            self.time_offset = None

            # zdefiniowanie wartości dla przesunięć, wysokości i szerokości
            # każdego elementu na ekranie

            # offset od lewej ekranu
            self.x_offset = 400
            self.track_bar_height = int(config.screen_height * 0.85)
            self.track_bar_width = 12
            self.horizontal_bar_height = 8

            self.note_width = 50
            # powiekszenie strzałki, gdy zostanie trafiona
            self.zoom_scale = 1.2
            # ustawienie strzałek aby były na środku ścieżki
            self.note_xoffset = (self.track_bar_width - self.note_width) / 2
            self.note_xoffset_large = (self.track_bar_width - self.note_width * self.zoom_scale) / 2

            # strzałki przewijają sie od góry do dołu
            # 3.0 to czas w jakim wędrują po ekranie
            self.note_offset = 3.0
            self.note_speed = config.screen_height / self.note_offset

            # ilość torów
            self.num_track_bars = 4
            self.track_bar_spacing = (config.screen_width - self.x_offset * 2) / (self.num_track_bars - 1)
            self.track_xoffsets = {
            track_idx: self.x_offset + track_idx * self.track_bar_spacing
            for track_idx in range(self.num_track_bars)
            }

            self.onset_times = self.read_beatmap_file(beatmap_path)
            # możn pomijać onset, aby dostosować poziom trudności
            # pominiecie co drugiego onset sprawi że strzałki będą mnie zbite
            # self.onset_times = self.onset_times[::2]

            self.num_notes = len(self.onset_times)
            # przypisanie ścieżki do strzałki
            # renpy.random.randint is upper-inclusive
            self.random_track_indices = [
            renpy.random.randint(0, self.num_track_bars - 1) for _ in range(self.num_notes)
            ]

            self.active_notes_per_track = {
            track_idx: [] for track_idx in range(self.num_track_bars)
            }

            # wykrywanie i rejestrowanie trafień
            self.onset_hits = {
            onset: False for onset in self.onset_times
            }
            self.num_hits = 0
            # trafienie jest liczone jeśli nuta zostanie uderzona w ciągu 0,3
            # sekundy od jej rzeczywistego czasu rozpoczęcia
            self.hit_threshold = 0.3 # seconds


            self.keycode_to_track_idx = {
            pygame.K_LEFT: 0,
            pygame.K_UP: 1,
            pygame.K_DOWN: 2,
            pygame.K_RIGHT: 3
            }

            self.track_bar_drawable = Solid('#fff', xsize=self.track_bar_width, ysize=self.track_bar_height)
            self.horizontal_bar_drawable = Solid('#fff', xsize=config.screen_width, ysize=self.horizontal_bar_height)
            # przypisanie grafik strzałek
            self.note_drawables = {
            0: Image('leftArrow.png'),
            1: Image('upArrow.png'),
            2: Image('downArrow.png'),
            3: Image('rightArrow.png')
            }

            self.note_drawables_large = {
            0: Transform(self.note_drawables[0], zoom=self.zoom_scale),
            1: Transform(self.note_drawables[1], zoom=self.zoom_scale),
            2: Transform(self.note_drawables[2], zoom=self.zoom_scale),
            3: Transform(self.note_drawables[3], zoom=self.zoom_scale),
            }

            self.drawables = [
            self.track_bar_drawable,
            self.horizontal_bar_drawable,
            ]
            self.drawables.extend(list(self.note_drawables.values()))
            self.drawables.extend(list(self.note_drawables_large.values()))

        def render(self, width, height, st, at):
            """
            st: A float, the shown timebase, in seconds.
            The shown timebase begins when this displayable is first shown on the screen.
            """
            if self.time_offset is None:
                self.time_offset = st
                # rozpoczęcie muzyki
                renpy.music.play(self.audio_path, loop=False)
                self.has_started = True

            render = renpy.Render(width, height)

            # rysowanie poziomych ścieżek
            for track_idx in range(self.num_track_bars):
                x_offset = self.track_xoffsets[track_idx]
                render.place(self.track_bar_drawable, x=x_offset, y=0)

            # poziomy pasek, aby wskazujący, gdzie kończy się ścieżka
            # x = 0 od lewej
            render.place(self.horizontal_bar_drawable, x=0, y=self.track_bar_height)


            if self.has_started:
                # sprawdzenie czy piosenka sie skonczyla
                if renpy.music.get_playing() is None:
                    self.has_ended = True
                    renpy.timeout(0)
                    return render

                # liczba sekund, przez które utwór był odtwarzany
                # jest różnicą między bieżącym wyświetlanym czasem a buforowanym pierwszym st
                curr_time = st - self.time_offset
                self.active_notes_per_track = self.get_active_notes_per_track(curr_time)

                for track_idx in self.active_notes_per_track:
                    x_offset = self.track_xoffsets[track_idx]

                    # loop through active notes
                    for onset, note_timestamp in self.active_notes_per_track[track_idx]:
                        # renderowanie strzałek, które są aktywne ale nie były trafione
                        if self.onset_hits[onset] is False:
                            if abs(curr_time - onset) <= self.hit_threshold:
                                note_drawable = self.note_drawables_large[track_idx]
                                note_xoffset = x_offset + self.note_xoffset_large
                            else:
                                note_drawable = self.note_drawables[track_idx]
                                note_xoffset = x_offset + self.note_xoffset

                            # obliczenie pionowej osi strzałek
                            # pionowa odległość od góry, którą przemieściła się strzałka
                            note_distance_from_top = note_timestamp * self.note_speed
                            y_offset = self.track_bar_height - note_distance_from_top
                            render.place(note_drawable, x=note_xoffset, y=y_offset)
                        else:
                            continue

            renpy.redraw(self, 0)
            return render

        def event(self, ev, x, y, st):
            if self.has_ended:
                # odświeżenie ekranu
                renpy.restart_interaction()
                return
            # sprawdzenie czy któryś przycisk został trafiony
            if ev.type == pygame.KEYDOWN:
                if not ev.key in self.keycode_to_track_idx:
                    return
                track_idx = self.keycode_to_track_idx[ev.key]

                active_notes_on_track = self.active_notes_per_track[track_idx]
                curr_time = st - self.time_offset

                # pętlna po aktywnych sktrzałkach w celu sprawdzenia, czy któraś została trafiona
                for onset, _ in active_notes_on_track:
                    # obliczenie różnicy czasu między momentem naciśnięcia klawisza a momentem, w którym uważamy, że nuta jest uderzana
                    if abs(curr_time - onset) <= self.hit_threshold:
                        self.onset_hits[onset] = True
                        self.num_hits += 1
                        # redraw natychmiast, ponieważ strzałka powinna zniknąć z ekranu
                        renpy.redraw(self, 0)
                        renpy.restart_interaction()

        def visit(self):
            return self.drawables

        def get_active_notes_per_track(self, current_time):
            active_notes = {
            track_idx: [] for track_idx in range(self.num_track_bars)
            }

            for onset, track_idx in zip(self.onset_times, self.random_track_indices):
                time_before_appearance = onset - current_time
                if time_before_appearance < 0:
                    continue
                elif time_before_appearance <= self.note_offset:
                    active_notes[track_idx].append((onset, time_before_appearance))
                elif time_before_appearance > self.note_offset:
                    break

            return active_notes

        def read_beatmap_file(self, beatmap_path):
            beatmap_path_full = os.path.join(config.gamedir, beatmap_path)
            with open(beatmap_path_full, 'rt') as f:
                text = f.read()
            onset_times = [float(string) for string in text.split('\n') if string != '']
            return onset_times