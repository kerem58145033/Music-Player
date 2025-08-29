import sys
import os
from PyQt5.QtWidgets import (QApplication, QMainWindow, QWidget, QPushButton, QVBoxLayout, QHBoxLayout, QListWidget, QFileDialog, QLabel, QSlider)
from PyQt5.QtCore import Qt, QUrl, QTimer
from PyQt5.QtMultimedia import QMediaPlayer, QMediaContent
from PyQt5.QtGui import QPixmap
from mutagen.mp3 import MP3
from mutagen.id3 import ID3, APIC
from PIL import Image
import io

from PyQt5.QtWidgets import QInputDialog

LANGUAGES = {
	'English': {
		'title': 'PyQt5 Music Player',
		'play': 'Play',
		'pause': 'Pause',
		'stop': 'Stop',
		'next': 'Next',
		'prev': 'Previous',
		'add': 'Add Songs',
		'no_song': 'No song playing',
		'volume': 'Volume',
		'open_files': 'Open Music Files',
		'audio_files': 'Audio Files (*.mp3 *.wav *.ogg)',
		'no_art': 'No Art',
		'lang_select': 'Select Language',
	},
	'Türkçe': {
		'title': 'PyQt5 Müzik Çalar',
		'play': 'Oynat',
		'pause': 'Duraklat',
		'stop': 'Durdur',
		'next': 'Sonraki',
		'prev': 'Önceki',
		'add': 'Şarkı Ekle',
		'no_song': 'Şarkı çalmıyor',
		'volume': 'Ses',
		'open_files': 'Müzik Dosyalarını Aç',
		'audio_files': 'Ses Dosyaları (*.mp3 *.wav *.ogg)',
		'no_art': 'Kapak Yok',
		'lang_select': 'Dil Seçimi',
	}
}

class MusicPlayer(QMainWindow):
	def __init__(self):
		super().__init__()
		# Language selection
		lang, ok = QInputDialog.getItem(self, LANGUAGES['English']['lang_select'], LANGUAGES['English']['lang_select'], list(LANGUAGES.keys()), 0, False)
		if not ok:
			lang = 'English'
		self.lang = lang
		self.texts = LANGUAGES[self.lang]

		self.setWindowTitle(self.texts['title'])
		self.setGeometry(200, 200, 600, 400)

		self.player = QMediaPlayer()
		self.playlist = []
		self.current_index = -1

		self.init_ui()
		self.scan_songs_folder()

	def scan_songs_folder(self):
		songs_dir = os.path.join(os.getcwd(), 'songs')
		if not os.path.exists(songs_dir):
			os.makedirs(songs_dir)
		supported_exts = ('.mp3', '.wav', '.ogg')
		for fname in os.listdir(songs_dir):
			if fname.lower().endswith(supported_exts):
				fpath = os.path.join(songs_dir, fname)
				if fpath not in self.playlist:
					self.playlist.append(fpath)
					self.list_widget.addItem(fname)

	def init_ui(self):
		main_widget = QWidget()
		self.setCentralWidget(main_widget)

		# Album art
		self.album_art = QLabel()
		self.album_art.setFixedSize(150, 150)
		self.album_art.setStyleSheet("border: 1px solid #aaa; background: #eee;")
		self.album_art.setAlignment(Qt.AlignCenter)
		self.set_default_album_art()

		# Song list
		self.list_widget = QListWidget()
		self.list_widget.doubleClicked.connect(self.play_selected_song)

		# Buttons
		self.play_btn = QPushButton(self.texts['play'])
		self.pause_btn = QPushButton(self.texts['pause'])
		self.stop_btn = QPushButton(self.texts['stop'])
		self.next_btn = QPushButton(self.texts['next'])
		self.prev_btn = QPushButton(self.texts['prev'])
		self.add_btn = QPushButton(self.texts['add'])

		self.play_btn.clicked.connect(self.play_song)
		self.pause_btn.clicked.connect(self.pause_song)
		self.stop_btn.clicked.connect(self.stop_song)
		self.next_btn.clicked.connect(self.next_song)
		self.prev_btn.clicked.connect(self.prev_song)
		self.add_btn.clicked.connect(self.add_songs)

		# Song label
		self.song_label = QLabel(self.texts['no_song'])
		self.song_label.setAlignment(Qt.AlignCenter)

		# Progress slider and time labels
		self.slider = QSlider(Qt.Horizontal)
		self.slider.setRange(0, 0)
		self.slider.sliderMoved.connect(self.set_position)
		self.player.positionChanged.connect(self.position_changed)
		self.player.durationChanged.connect(self.duration_changed)

		self.time_label = QLabel("00:00:00:00")
		self.time_label.setAlignment(Qt.AlignRight)

		# Volume slider
		self.volume_slider = QSlider(Qt.Horizontal)
		self.volume_slider.setRange(0, 100)
		self.volume_slider.setValue(50)
		self.volume_slider.valueChanged.connect(self.set_volume)
		self.player.setVolume(50)

		# Layouts
		controls_hbox = QHBoxLayout()
		controls_hbox.addWidget(self.prev_btn)
		controls_hbox.addWidget(self.play_btn)
		controls_hbox.addWidget(self.pause_btn)
		controls_hbox.addWidget(self.stop_btn)
		controls_hbox.addWidget(self.next_btn)
		controls_hbox.addWidget(self.add_btn)

		right_vbox = QVBoxLayout()
		right_vbox.addWidget(self.song_label)
		slider_hbox = QHBoxLayout()
		slider_hbox.addWidget(self.slider)
		slider_hbox.addWidget(self.time_label)
		right_vbox.addLayout(slider_hbox)
		right_vbox.addWidget(self.list_widget)
		right_vbox.addLayout(controls_hbox)
		right_vbox.addWidget(QLabel(self.texts['volume']))
		right_vbox.addWidget(self.volume_slider)

		main_hbox = QHBoxLayout()
		main_hbox.addWidget(self.album_art)
		main_hbox.addLayout(right_vbox)

		main_widget.setLayout(main_hbox)

	def set_default_album_art(self):
		# Set a default placeholder for album art
		self.album_art.setText(self.texts['no_art'])

	def add_songs(self):
		songs_dir = os.path.join(os.getcwd(), 'songs')
		if not os.path.exists(songs_dir):
			os.makedirs(songs_dir)
		files, _ = QFileDialog.getOpenFileNames(self, self.texts['open_files'], '', self.texts['audio_files'])
		for file in files:
			base_name = os.path.basename(file)
			dest_path = os.path.join(songs_dir, base_name)
			# Copy file if not already in songs folder
			if not os.path.exists(dest_path):
				try:
					with open(file, 'rb') as src, open(dest_path, 'wb') as dst:
						dst.write(src.read())
				except Exception as e:
					print(f"Failed to copy {file}: {e}")
					continue
			if dest_path not in self.playlist:
				self.playlist.append(dest_path)
				self.list_widget.addItem(base_name)
		# If nothing is playing, start playing the first song
		if self.current_index == -1 and self.playlist:
			self.current_index = 0
			self.play_song()

	def play_selected_song(self):
		self.current_index = self.list_widget.currentRow()
		self.play_song()

	def play_song(self):
		if not self.playlist:
			return
		if self.current_index == -1:
			self.current_index = 0
		song = self.playlist[self.current_index]
		self.player.setMedia(QMediaContent(QUrl.fromLocalFile(song)))
		self.player.play()
		self.song_label.setText(os.path.basename(song))
		self.list_widget.setCurrentRow(self.current_index)
		self.update_album_art(song)

	def update_album_art(self, song_path):
		# Try to load album art from the same folder as the song (jpg/png with same basename)
		base, ext = os.path.splitext(song_path)
		for img_ext in ('.jpg', '.png', '.jpeg'):
			img_path = base + img_ext
			if os.path.exists(img_path):
				pixmap = QPixmap(img_path)
				pixmap = pixmap.scaled(self.album_art.width(), self.album_art.height(), Qt.KeepAspectRatio, Qt.SmoothTransformation)
				self.album_art.setPixmap(pixmap)
				return
		# Try to extract album art from mp3 file
		if ext.lower() == '.mp3':
			try:
				audio = MP3(song_path, ID3=ID3)
				if audio.tags is not None:
					for tag in audio.tags.values():
						if isinstance(tag, APIC):
							img_data = tag.data
							image = Image.open(io.BytesIO(img_data))
							image = image.resize((self.album_art.width(), self.album_art.height()), Image.LANCZOS)
							buf = io.BytesIO()
							image.save(buf, format='PNG')
							qt_img = QPixmap()
							qt_img.loadFromData(buf.getvalue(), 'PNG')
							self.album_art.setPixmap(qt_img)
							return
			except Exception as e:
				print(f"Failed to extract album art: {e}")
		self.set_default_album_art()

	def set_volume(self, value):
		self.player.setVolume(value)

	def pause_song(self):
		self.player.pause()

	def stop_song(self):
		self.player.stop()
		self.song_label.setText(self.texts['no_song'])

	def next_song(self):
		if not self.playlist:
			return
		self.current_index = (self.current_index + 1) % len(self.playlist)
		self.play_song()

	def prev_song(self):
		if not self.playlist:
			return
		self.current_index = (self.current_index - 1) % len(self.playlist)
		self.play_song()

	def position_changed(self, position):
		self.slider.setValue(position)
		self.update_time_label(position, self.player.duration())

	def duration_changed(self, duration):
		self.slider.setRange(0, duration)
		self.update_time_label(self.player.position(), duration)

	def update_time_label(self, position, duration):
		def ms_to_min_sec(ms):
			s = int(ms // 1000)
			return f"{s//60:02}:{s%60:02}"
		pos_str = ms_to_min_sec(position)
		dur_str = ms_to_min_sec(duration) if duration > 0 else "00:00"
		self.time_label.setText(f"{pos_str}/{dur_str}")

	def set_position(self, position):
		self.player.setPosition(position)

if __name__ == '__main__':
	app = QApplication(sys.argv)
	window = MusicPlayer()
	window.show()
	sys.exit(app.exec_())
