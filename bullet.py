import pygame
from pygame.sprite import Sprite
from random import randint


class Bullet(Sprite):
	"""宇宙船から発射される弾に関するクラス"""

	def __init__(self, ai_game, x_dir=0):
		"""宇宙船の現在の一から弾のオブジェクトを生成する"""
		super().__init__()
		self.screen = ai_game.screen
		self.settings = ai_game.settings
		self.color = self.settings.bullet_color

		# 弾のrectを(0, 0)の位置に作成してから、正しい位置を設定する
		self.rect = pygame.Rect(0, 0, self.settings.bullet_width, self.settings.bullet_height)
		self.rect.midtop = ai_game.ship.rect.midtop

		# 弾の位置を浮動小数点数で保存する
		self.y = float(self.rect.y)
		self.x = float(self.rect.x)
		self.x_dir = x_dir

	def update(self):
		"""画面上の弾を移動する"""
		# 弾の浮動小数点数での緯度を更新する
		self.y -= self.settings.bullet_speed
		self.x -= self.x_dir * 0.3
		# rectの位置を更新する
		self.rect.y = self.y
		self.rect.x = int(self.x)

	def draw_bullet(self):
		"""画面に弾を描画する"""
		pygame.draw.rect(self.screen, self.color, self.rect)


class Bomb:
	BULLET = 0
	BOMB = 1

	def __init__(self, ai_game):
		self.settings = ai_game.settings
		self.screen = ai_game.screen
		self.color = self.settings.bomb_color
		self.cx, self.cy = ai_game.ship.rect.midtop
		self.cy -= randint(100, 700)
		self.r = 0

		self.limit = self.settings.bomb_r * 5 + 50
		self.bullet = Bullet(ai_game)
		self.bullet.color = self.settings.bomb_color
		self.bullet_x_dir = 1
		self.bullet.x -= 4
		self.bullet_x_dir_count = 0
		self.mode = self.BULLET

	def update(self):
		if self.mode == self.BOMB:
			self.limit -= 1
			if self.r < self.settings.bomb_r:
				self.r += 0.2
		self.bullet.update()
		self.bullet.x += self.bullet_x_dir
		self.bullet_x_dir_count += 1
		if self.bullet_x_dir_count == 8:
			self.bullet_x_dir_count = 0
			self.bullet_x_dir *= -1
		if self.mode == self.BULLET and self.bullet.y < self.cy:
			self.mode = self.BOMB

	def draw_bomb(self):
		if self.mode == self.BULLET:
			self.bullet.draw_bullet()
		elif self.mode == self.BOMB:
			pygame.draw.circle(
				surface=self.screen,
				color=self.color,
				center=(self.cx, self.cy),
				radius=self.r
			)
