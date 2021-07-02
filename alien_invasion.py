import sys
from time import sleep, time

import pygame

from setting import Settings
from ship import Ship
from game_stats import GameStats
from button import Button
from bullet import Bullet
from bullet import Bomb
from alien import Alien
from laser_beam import LaserBeam


class AlienInvasion:
	"""ゲームのアセットと動作を管理する全体的なクラス"""

	def __init__(self):
		"""ゲームを初期化し、ゲームのリソースを作成する"""
		pygame.init()
		self.settings = Settings()

		self.start_time = time()

		# 以下3行でsurfaceをフルスクリーンで表示する
		# self.screen = pygame.display.set_mode((0, 0), pygame.FULLSCREEN)
		# self.settings.screen_width = self.screen.get_rect().width
		# self.settings.screen_height = self.screen.get_rect().height
		self.screen = pygame.display.set_mode(
			(self.settings.screen_width, self.settings.screen_height))
		pygame.display.set_caption("エイリアン侵略")

		# ゲームの統計情報を格納するインスタンスを生成する
		self.stats = GameStats(self)

		self.ship = Ship(self)
		self.bullets = pygame.sprite.Group()
		self.aliens = pygame.sprite.Group()
		self.bomb = None
		self.laser = None

		self.font = pygame.font.Font(None, self.settings.font_size)

		self._create_fleet()

		# Playボタンを作成する
		self.play_button = Button(self, "Play")

	def run_game(self):
		"""ゲームのメインループを開始する"""
		while True:
			self._check_events()

			if self.stats.game_active:
				self.ship.update()
				self._update_bullets()
				self._update_bomb()
				self._update_laser()
				self._update_aliens()

			self._update_screen()

	def _check_events(self):
		# キーボードとマウスのイベントに対応する
		for event in pygame.event.get():
			if event.type == pygame.QUIT:
				sys.exit()
			elif event.type == pygame.MOUSEBUTTONDOWN:
				mouse_pos = pygame.mouse.get_pos()
				self._check_play_button(mouse_pos)
			elif event.type == pygame.KEYDOWN:
				self._check_keydown_events(event)
			elif event.type == pygame.KEYUP:
				self._check_keyup_events(event)

	def _check_keydown_events(self, event):
		"""キーを押すイベントに対応する"""
		if self.stats.game_active:
			if event.key == pygame.K_RIGHT:
				self.ship.moving_right = True
			elif event.key == pygame.K_LEFT:
				self.ship.moving_left = True
			elif event.key == pygame.K_SPACE:
				self._fire_bullet()
			elif event.key == pygame.K_f:
				self._fire_bullets()
			elif event.key == pygame.K_b and self.bomb is None:
				self.bomb = Bomb(self)
			elif event.key == pygame.K_x and self.laser is None:
				self.laser = LaserBeam(self)
		if event.key == pygame.K_q:
			sys.exit()

	def _check_keyup_events(self, event):
		"""キーを離すイベントに対応する"""
		if self.stats.game_active:
			if event.key == pygame.K_RIGHT:
				self.ship.moving_right = False
			elif event.key == pygame.K_LEFT:
				self.ship.moving_left = False

	def _check_play_button(self, mouse_pos):
		"""プレイヤーがPlayボタンをクリックしたら新規ゲームを開始する"""
		if self.play_button is not None:
			if self.play_button.rect.collidepoint(mouse_pos):
				self.stats.game_active = True
				self.aliens.empty()
				self.bullets.empty()
				self.bomb = None
				self.laser = None
				self.stats.reset_stats()
				self.play_button = None
				self.start_time = time()

	def _fire_bullet(self):
		"""新しい弾を作成し、bulletsグループに追加する"""
		if len(self.bullets) < self.settings.bullets_allowed:
			new_bullet = Bullet(self)
			self.bullets.add(new_bullet)

	def _fire_bullets(self):
		if len(self.bullets) < self.settings.bullets_allowed:
			for i in range(5):
				new_bullet = Bullet(self, x_dir=i - 2)
				new_bullet.color = (0, 150, 150)
				self.bullets.add(new_bullet)

	def _update_bullets(self):
		"""弾の位置を更新し、古い弾を廃棄する"""
		# 弾の位置を更新する
		self.bullets.update()

		# 見えなくなった弾を廃棄する
		for bullet in self.bullets.copy():
			if bullet.rect.bottom <= 0:
				self.bullets.remove(bullet)

		self._check_bullet_alien_collisions()

	def _check_bullet_alien_collisions(self):
		"""弾とエイリアンの衝突に対応する"""
		# 衝突した弾とエイリアンを削除する
		collisions = pygame.sprite.groupcollide(
			self.bullets, self.aliens, True, True)

		if not self.aliens:
			# 存在する弾を破壊し、新しい艦隊を作成する
			self.bullets.empty()
			self._create_fleet()
			self.bomb = None
			self.laser = None

	def _update_bomb(self):
		if self.bomb is not None:
			self.bomb.update()
			bomb_r = self.bomb.r ** 2
			for alien in self.aliens:
				distances = [
					(alien.rect.left - self.bomb.cx) ** 2 + (alien.rect.top - self.bomb.cy) ** 2,
					(alien.rect.left - self.bomb.cx) ** 2 + (alien.rect.bottom - self.bomb.cy) ** 2,
					(alien.rect.right - self.bomb.cx) ** 2 + (alien.rect.top - self.bomb.cy) ** 2,
					(alien.rect.right - self.bomb.cx) ** 2 + (alien.rect.bottom - self.bomb.cy) ** 2
				]
				for distance in distances:
					if distance < bomb_r:
						self.aliens.remove(alien)
			if self.bomb.limit == 0:
				self.bomb = None

	def _update_laser(self):
		if self.laser is not None:
			self.laser.update(self)
			for alien in self.aliens:
				# 当たり判定x座標だけ見ればいいからこれでいいはず。
				# ボムのやつは円だったから円の中心とエイリアンの四つ角それぞれの距離を計算してた。
				frags = [
					alien.rect.right >= self.laser.rect.left -
					self.settings.laser_width * self.settings.laser_ball_width_rate + 5,
					alien.rect.left <= self.laser.rect.right +
					self.settings.laser_width * self.settings.laser_ball_width_rate - 5
				]
				# if alien.rect.right >= self.laser.rect.left and alien.rect.left <= self.laser.rect.right:
				if frags[0] and frags[1]:
					self.aliens.remove(alien)
			if self.laser.limit == 0:
				self.laser = None

	def _update_aliens(self):
		"""
		艦隊が画面の隣にいるか確認してから
		艦隊にいる全エイリアンの位置を更新する
		"""
		self._check_fleet_edges()
		self.aliens.update()

		# エイリアンと宇宙船の衝突を探す
		if pygame.sprite.spritecollideany(self.ship, self.aliens):
			self._ship_hit()

		# 画面の一番下に到達したエイリアンを探す
		self._check_aliens_bottom()

	def _create_fleet(self):
		"""エイリアンの艦隊を作成する"""

		# 各エイリアンの間にはエイリアンの1匹分のスペースを空ける
		alien = Alien(self)
		alien_width, alien_height = alien.rect.size
		available_space_x = self.settings.screen_width - (2 * alien_width)
		number_aliens_x = available_space_x // (2 * alien_width)

		# 画面に収まるエイリアンの列数を決定する
		ship_height = self.ship.rect.height
		available_space_y = (self.settings.screen_height - (3 * alien_height) - ship_height)
		number_rows = available_space_y // (2 * alien_height)

		# エイリアンの艦隊を作成する
		for row_number in range(number_rows):
			for alien_number in range(number_aliens_x):
				self._create_alien(alien_number, row_number)

	def _create_alien(self, alien_number, row_number):
		# エイリアンを1匹作成し、列の中に配置する
		alien = Alien(self)
		alien_width, alien_height = alien.rect.size
		alien.x = alien_width + 2 * alien_width * alien_number
		alien.rect.x = alien.x
		alien.rect.y = alien_height + 2 * alien_height * row_number
		self.aliens.add(alien)

	def _check_fleet_edges(self):
		"""エイリアンが画面の端に達した場合に適切な処理を行う"""
		for alien in self.aliens.sprites():
			if alien.check_edges():
				self._change_fleet_direction()
				break

	def _change_fleet_direction(self):
		"""艦隊を下に移動し、横移動の方向を変更する"""
		for alien in self.aliens.sprites():
			alien.rect.y += self.settings.fleet_drop_speed
		self.settings.fleet_direction *= -1

	def _ship_hit(self):
		"""エイリアンと宇宙船の衝突に対応する"""
		# 残りの宇宙船の数を減らす↓ここだと思う
		self.stats.ships_left -= 1

		if self.stats.ships_left > 0:
			# # 残りの宇宙船の数を減らす
			# self.stats.ships_left -= 1
			# この処理ifの前じゃない？？

			# 残ったエイリアンと弾を廃棄する
			self.aliens.empty()
			self.bullets.empty()
			self.bomb = None
			self.laser = None

			# 新しいエイリアンと弾を廃棄する
			self._create_fleet()
			self.ship.center_ship()

			# 一時停止する
			sleep(0.5)
		else:
			self.play_button = Button(self, "Replay")
			self.stats.game_active = False

	def _check_aliens_bottom(self):
		"""エイリアンが画面の一番下に到達したかを確認する"""
		screen_rect = self.screen.get_rect()
		for alien in self.aliens.sprites():
			if alien.rect.bottom >= screen_rect.bottom:
				# 宇宙船を破壊した時と同じように動作する
				self._ship_hit()
				break

	def _update_screen(self):
		"""画面上の画像を更新し、新しい画面に切り替える"""
		self.screen.fill(self.settings.bg_color)
		self.ship.blitme()
		for bullet in self.bullets.sprites():
			bullet.draw_bullet()
		if self.bomb is not None:
			self.bomb.draw_bomb()
		self.aliens.draw(self.screen)
		self._draw_ships_left()
		if self.laser is not None:
			self.laser.draw_laser_beam()
		if self.stats.ships_left == 0:
			self._draw_game_over()

		# ゲームが非アクティブ状態の時に、「Play」ボタンを描画する
		if not self.stats.game_active:
			self.play_button.draw_button()
		else:
			self._draw_time()

		pygame.display.flip()

	def _draw_ships_left(self):
		color = (0, 0, 0)
		if self.settings.mode == self.settings.DARK:
			color = (255, 255, 255)
		text = self.font.render(f"ship × {self.stats.ships_left}", True, color)
		self.screen.blit(text, [0, 0])

	def _draw_game_over(self):
		font = pygame.font.Font(None, self.settings.font_size * 2)
		font.bold = True
		font.italic = True
		font.underline = True
		text = font.render("GAME OVER", True, (255, 0, 0))
		self.screen.blit(text, [
			self.settings.screen_width // 2 - self.settings.font_size * 5,
			self.settings.screen_height // 2 - self.settings.font_size
		])

	def _draw_time(self):
		font = pygame.font.Font(None, self.settings.font_size)
		font.bold = True
		font.italic = True
		color = (0, 0, 0)
		if self.settings.mode == self.settings.DARK:
			color = (255, 255, 255)
		text = font.render(f"{int(time() - self.start_time)}".zfill(3), True, color)
		self.screen.blit(text, [self.settings.screen_width - self.settings.font_size * 3, 0])


if __name__ == '__main__':
	# ゲームのインスタンスを作成し、ゲームを実行する
	ai = AlienInvasion()
	ai.run_game()
