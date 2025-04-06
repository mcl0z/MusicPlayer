import ctypes
import random
import threading
import os
import sys
import time
import mutagen
from mutagen.mp3 import MP3
from mutagen.id3 import ID3
sys.stdout = open('nul', 'w')
import pygame
import pygame.gfxdraw
sys.stdout.close()
sys.stdout = sys.__stdout__
from PIL import Image
from math import floor
import io
import re
import math

def parse_file(path):
    '''This function parses the ID3 information from the song, encompassing details such as the title, artist, album, and image.
    It returns a tuple in the following format: ('mp3 file name', 'music title', 'artist', 'album', music length(float), [binary image data], lyrics).
    NOTE: If there isn't information in the file, it returns None instead of string.'''
    audiofile = None
    title = None
    artist = None
    album = None
    length = 0.6
    picture = None
    lyrics = None

    audiofile = mutagen.File(path)
    if audiofile and 'TIT2' in audiofile:    title  = audiofile.tags['TIT2'].text[0] # try to get music title
    if audiofile and 'TPE1' in audiofile:    artist = audiofile.tags['TPE1'].text[0] # try to get music artist
    if audiofile and 'TALB' in audiofile:    album  = audiofile.tags['TALB'].text[0] # try to get music album
    
    # 尝试读取歌词
    try:
        id3 = ID3(path)
        if 'USLT::eng' in id3:
            lyrics = id3['USLT::eng'].text
        elif 'USLT::XXX' in id3:
            lyrics = id3['USLT::XXX'].text
        elif len(id3.getall('USLT')) > 0:
            lyrics = id3.getall('USLT')[0].text
    except:
        lyrics = None
    
    # 如果MP3文件没有嵌入歌词，则尝试从外部文件导入歌词
    if lyrics is None or lyrics == '':
        # 尝试查找与音乐文件同名的外部歌词文件
        external_lyrics = find_external_lyrics(path)
        if external_lyrics:
            lyrics = external_lyrics
    
    try:
        length = MP3(path).info.length # will raise error when music length is 0
    except: # im too lazy to explain the error type :\
        pass # length defaults to 0.6
    if audiofile and 'APIC:' in audiofile: picture = audiofile.tags['APIC:'].data # try to get music album picture

    if title == '':
        title = None
    if artist == '':
        artist = None
    if album == '':
        album = None

    return os.path.basename(path), title, artist, album, length, picture, lyrics

def find_external_lyrics(music_path):
    """查找与音乐文件同名的外部歌词文件"""
    # 支持的歌词文件扩展名
    lyric_extensions = ['.lrc', '.txt', '.krc']
    
    # 获取音乐文件名（不含扩展名）
    music_dir = os.path.dirname(music_path)
    music_basename = os.path.splitext(os.path.basename(music_path))[0]
    
    # 在音乐目录中查找同名的歌词文件
    for ext in lyric_extensions:
        lyric_path = os.path.join(music_dir, music_basename + ext)
        if os.path.exists(lyric_path):
            try:
                # 尝试读取歌词文件内容
                with open(lyric_path, 'r', encoding='utf-8') as f:
                    return f.read()
            except UnicodeDecodeError:
                # 如果UTF-8解码失败，尝试使用GBK编码
                try:
                    with open(lyric_path, 'r', encoding='gbk') as f:
                        return f.read()
                except:
                    print(f"无法读取歌词文件: {lyric_path}")
            except Exception as e:
                print(f"读取歌词文件出错: {lyric_path}, 错误: {e}")
    
    # 没有找到歌词文件
    return None

def parse_lyrics(lyrics_text):
    """解析歌词文本，返回时间标记和对应的歌词内容"""
    if not lyrics_text:
        return []
    
    # 检测是否是LRC格式歌词
    if "[" in lyrics_text and "]" in lyrics_text and re.search(r'\[\d+:\d+\.\d+\]', lyrics_text):
        # 尝试匹配LRC格式的歌词时间标记 [mm:ss.xx]
        pattern = r'\[(\d+):(\d+)\.(\d+)\](.*?)\n'
        matches = re.findall(pattern, lyrics_text + '\n')
        
        result = []
        for match in matches:
            minutes = int(match[0])
            seconds = int(match[1])
            milliseconds = int(match[2])
            time_in_seconds = minutes * 60 + seconds + milliseconds / 100
            lyric_text = match[3].strip()
            
            # 过滤空行
            if lyric_text and not lyric_text.isspace():
                result.append((time_in_seconds, lyric_text))
    else:
        # 如果不是LRC格式，按行分割作为普通文本处理
        result = []
        lines = lyrics_text.strip().split('\n')
        # 为每行分配一个固定的时间间隔（每5秒一行）
        for i, line in enumerate(lines):
            if line.strip() and not line.strip().isspace():  # 过滤空行
                result.append((i * 5.0, line.strip()))
    
    return sorted(result)

def get_background():
    '''This function returns a path randomly. Like: ./Resources/backgrounds/snow/day.png'''
    path = './Resources/backgrounds'
    dirs = os.listdir(path)
    # 0:00 ~ 10:00 day.png
    # 10:00 ~ 17:00 noon.png
    # 17:00 ~ 23:59 night.png
    hour = time.localtime().tm_hour
    min = time.localtime().tm_min

    is_day = 0 <= hour <= 9 and 0 <= min <= 59
    is_noon = 10 <= hour <= 16 and 0 <= min <= 59
    is_night = 17 <= hour <= 23

    if is_day:
        # DAY
        return './Resources/backgrounds/{}/day.png'.format(random.choice(dirs))
    elif is_noon:
        # NOON
        return './Resources/backgrounds/{}/noon.png'.format(random.choice(dirs))
    elif is_night:
        # NIGHT
        return './Resources/backgrounds/{}/night.png'.format(random.choice(dirs))

def get_note():
    '''This function returns a path randomly. Like: ./Resources/particles/note_blue.png'''
    path = './Resources/particles'
    dirs = os.listdir(path)
    return './Resources/particles/{}'.format(random.choices(dirs)[0])

def fade_in(surf: pygame.Surface, speed: int = 10, max_alpha: int = 255):
    if surf.get_alpha() < max_alpha: # fade in animation
        surf.set_alpha(surf.get_alpha() + speed)

def fade_out(surf: pygame.Surface, speed: int = 10, min_alpha: int = 0):
    if surf.get_alpha() > min_alpha: # fade out animation
        surf.set_alpha(surf.get_alpha() - speed)

def blur_in(speed: int = 1, max_blur_radius=10):
    global background_blur_radius, blurred_background
    if background_blur_radius < max_blur_radius: # blur in animation
            background_blur_radius += speed
            # 使用简单的暗化效果代替模糊
            blurred_background = background.copy()
            dark_overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
            dark_overlay.fill((0, 0, 0, min(background_blur_radius * 10, 100)))
            blurred_background.blit(dark_overlay, (0, 0))

def blur_out(speed: int = 1, min_blur_radius=0):
    global blurred_background, background_blur_radius
    if background_blur_radius > min_blur_radius: # blur animation
        background_blur_radius -= speed
        # 使用简单的暗化效果代替模糊
        blurred_background = background.copy()
        if background_blur_radius > 0:
            dark_overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
            dark_overlay.fill((0, 0, 0, min(background_blur_radius * 10, 100)))
            blurred_background.blit(dark_overlay, (0, 0))

def enter_animation():
    global total_progress_bar_width
    blur_in(speed=1, max_blur_radius=10)
            
    fade_in(info_background, speed=10, max_alpha=180)
    
    fade_in(album_cover, speed=30, max_alpha=255)

    fade_in(music_title_text, speed=10, max_alpha=255)
    
    fade_in(music_artist_text, speed=10, max_alpha=255)

    fade_in(music_pos_text, speed=10, max_alpha=255)

    fade_in(reversed_music_pos_text, speed=10, max_alpha=255)
    
    if total_progress_bar_width < album_cover.get_width(): # animation
        total_progress_bar_width += (album_cover.get_width() - total_progress_bar_width) / 5

def get_progress_bar_rect():
    """返回进度条的矩形区域，用于检测鼠标点击"""
    return pygame.Rect(WIDTH / 25, HEIGHT / 2 + 100 + 40 + 60, total_progress_bar_width, 10)

def is_mouse_over_progress_bar(mouse_pos):
    """检查鼠标是否在进度条区域内"""
    return get_progress_bar_rect().collidepoint(mouse_pos)

def set_music_position(mouse_x):
    """根据鼠标x坐标设置音乐播放位置"""
    global music_pos, music_start_time, target_progress_width, current_progress_width, is_big_jump, last_position
    
    if total_progress_bar_width <= 0:
        return
    
    # 记录上一个位置，用于判断是否是大幅跳转
    old_pos = music_pos
    
    # 计算相对位置
    progress_bar_left = WIDTH / 25
    relative_x = mouse_x - progress_bar_left
    
    # 确保在有效范围内
    if relative_x < 0:
        relative_x = 0
    elif relative_x > total_progress_bar_width:
        relative_x = total_progress_bar_width
    
    # 计算百分比位置
    position_percent = relative_x / total_progress_bar_width
    
    # 计算新的位置（秒）
    new_pos = position_percent * id3[4]
    
    # 判断是否是大幅跳转(>=20秒)
    is_big_jump = abs(new_pos - old_pos) >= 20.0
    
    # 暂停并重新开始音乐在新位置
    pygame.mixer.music.stop()
    pygame.mixer.music.play(start=new_pos)
    
    # 更新显示位置和开始计时的时间点
    music_pos = new_pos
    music_start_time = time.time() - new_pos
    
    # 设置进度条动画的目标宽度和初始宽度
    target_progress_width = relative_x
    current_progress_width = 0  # 从0开始填充

def update_note():
    global note_y, note_path, note
    with lock:  # 使用锁保护对共享资源的访问
        if round(note_y) - 0.1 <= 450: # show particle
            time.sleep(0.1)
            note_path = get_note()
            try:
                note = pygame.image.load(note_path).convert_alpha()
                note = pygame.transform.scale(note, (64, 64))
                note_y = HEIGHT / 2 + 50
            except Exception as e:
                print(f"加载音符图像出错: {e}")
        else:
            note_y -= 0.5  # 向上移动（恢复原来的向上浮动效果）
            time.sleep(0.01)

def paste_album_picture():
    global temp_album_cover
    if (id3[5] is None):
        img = Image.open('./Resources/icons/unknown_album.png')
    else:
        img = Image.open(io.BytesIO(id3[5]))
    for img_format in ['RGB', 'RGBA', 'RGBX', 'ARGB', 'BGRA', 'P']: # this list include priority (try RGB, RGBA first)
        try:
            temp_album_cover = pygame.image.frombytes(img.tobytes(), img.size, img_format).convert_alpha()
        except ValueError:
            continue # if ValueError, which means the album image is not this format
        else:
            break
    temp_album_cover = pygame.transform.smoothscale(temp_album_cover, (WIDTH / 3.4, WIDTH / 3.4))

def render_lyrics():
    """渲染歌词列表，Apple Music风格"""
    global lyrics_surface, lyrics_surfaces, current_lyric_index, parsed_lyrics
    
    if not parsed_lyrics:
        # 没有歌词时显示提示
        lyrics_surface = pygame.Surface((WIDTH / 2, HEIGHT), pygame.SRCALPHA)
        lyrics_surface.fill((0, 0, 0, 0))
        
        no_lyrics_text = medium_font.render("暂无歌词", True, (200, 200, 200))
        lyrics_surface.blit(no_lyrics_text, (lyrics_surface.get_width() // 2 - no_lyrics_text.get_width() // 2, 
                                           HEIGHT // 2 - no_lyrics_text.get_height() // 2))
        return
    
    # 创建歌词文本表面列表
    lyrics_surfaces = []
    for time_mark, lyric_text in parsed_lyrics:
        # 确保歌词文本不会太长
        if len(lyric_text) > 50:  # 限制长度，避免太长
            lyric_text = lyric_text[:47] + "..."
        
        # 使用中等大小字体渲染每行歌词
        text_surface = medium_font.render(lyric_text, True, (200, 200, 200))
        lyrics_surfaces.append(text_surface)
    
    # 创建歌词显示区域
    lyrics_surface = pygame.Surface((WIDTH / 2, HEIGHT), pygame.SRCALPHA)
    lyrics_surface.fill((0, 0, 0, 0))
    
    # 添加"歌词"标题
    lyrics_title = bold_font.render("歌词", True, (255, 255, 255))
    # 左对齐标题
    lyrics_surface.blit(lyrics_title, (20, 50))

# let program support high-dpi resolution
ctypes.windll.shcore.SetProcessDpiAwareness(1)
scale_factor = ctypes.windll.shcore.GetScaleFactorForDevice(0) / 125

if 1:
    WIDTH = int(1600 * scale_factor)
    HEIGHT = int(900 * scale_factor)
    SUPPORTED_FORMATS = ['mp3', 'ogg', 'wav']

    # pygame setup
    pygame.init() # Pygame, launch!
    
    # 启用GPU加速
    try:
        # 尝试启用硬件加速和垂直同步
        pygame.display.gl_set_attribute(pygame.GL_ACCELERATED_VISUAL, 1)
        pygame.display.gl_set_attribute(pygame.GL_DOUBLEBUFFER, 1)
        pygame.display.gl_set_attribute(pygame.GL_DEPTH_SIZE, 24)
        pygame.display.gl_set_attribute(pygame.GL_MULTISAMPLEBUFFERS, 0)
        pygame.display.gl_set_attribute(pygame.GL_MULTISAMPLESAMPLES, 0)  # 抗锯齿
        # 禁用垂直同步以获得更高帧率
        pygame.display.gl_set_attribute(pygame.GL_SWAP_CONTROL, 0)
        
        # 创建窗口
        screen = pygame.display.set_mode((WIDTH, HEIGHT), pygame.RESIZABLE | pygame.DOUBLEBUF | pygame.HWSURFACE | pygame.HWACCEL)
        
        # 设置优先级，让pygame获得更多处理时间
        if hasattr(pygame, 'high_priority'):
            pygame.high_priority()
    except:
        # 如果启用高级功能失败，使用基本设置
        print("高级GPU加速启用失败，使用基本设置")
        screen = pygame.display.set_mode((WIDTH, HEIGHT), pygame.RESIZABLE | pygame.DOUBLEBUF)
    
    pygame.display.set_caption('Music Player') # window title
    pygame.mixer.init() # init pygame mixer
    
    # 优化内存管理
    pygame.event.set_allowed([pygame.QUIT, pygame.KEYDOWN, pygame.DROPFILE, pygame.WINDOWRESIZED, 
                             pygame.MOUSEBUTTONDOWN, pygame.MOUSEBUTTONUP, pygame.MOUSEMOTION])
    
    # 其他初始化
    music_busy = False # True if there's music playing
    music_paused = False # True if music is paused
    music_pos: float = 0.0 # position of music (seconds)
    music_length: float = 0.0 # total length of music (seconds)
    music_start_time = 0.0 # 记录音乐开始播放的时间点
    music_paused_time = 0.0 # 记录音乐暂停时的时间点
    music_metadata = {} # metadata of music
    
    # 播放/暂停按钮
    play_pause_btn_radius = 30  # 按钮半径
    play_pause_btn_x = WIDTH / 25  # 按钮x坐标
    play_pause_btn_y = HEIGHT / 2 + 100 + 40 + 60 + 60  # 按钮y坐标，放在进度条下方
    is_playing = False  # 播放状态
    
    # 切歌按钮和循环播放按钮
    prev_btn_radius = 25  # 上一首按钮半径（比播放暂停按钮小）
    next_btn_radius = 25  # 下一首按钮半径
    loop_btn_radius = 25  # 循环播放按钮半径
    button_spacing = 80   # 按钮之间的间距

    prev_btn_x = play_pause_btn_x - button_spacing  # 上一首按钮x坐标（在播放暂停按钮左侧）
    prev_btn_y = play_pause_btn_y + (play_pause_btn_radius - prev_btn_radius)  # 稍微上移以对齐中心

    next_btn_x = play_pause_btn_x + play_pause_btn_radius * 2 + button_spacing - next_btn_radius * 2  # 下一首按钮x坐标
    next_btn_y = play_pause_btn_y + (play_pause_btn_radius - next_btn_radius)  # 与上一首按钮对齐

    loop_btn_x = next_btn_x + next_btn_radius * 2 + button_spacing - loop_btn_radius * 2  # 循环按钮x坐标
    loop_btn_y = play_pause_btn_y + (play_pause_btn_radius - loop_btn_radius)  # 与其他按钮对齐

    is_loop_enabled = False  # 循环播放状态
    current_music_index = -1  # 当前播放的歌曲在音乐库中的索引
    
    # 进度条动画相关变量
    target_progress_width = 0.0  # 目标进度条宽度
    current_progress_width = 0.0  # 当前进度条宽度
    
    # 歌词相关变量
    parsed_lyrics = []  # 解析后的歌词列表 [(时间, 歌词文本), ...]
    last_lyric_index = -1  # 上一次显示的歌词索引
    current_lyric_index = 0  # 当前高亮显示的歌词索引
    lyrics_surfaces = []  # 渲染后的歌词文本表面列表
    lyrics_surface = None  # 歌词显示区域
    is_big_jump = False  # 是否是大幅跳转，>=20秒
    
    # 预渲染的歌词表面
    full_lyrics_surface = None  # 缓存的完整歌词表面
    lyrics_area_width = 0  # 歌词区域宽度
    lyrics_need_update = True  # 是否需要更新歌词渲染
    gradient_overlay = None  # 缓存的渐变表面
    
    # 歌词动画相关变量
    target_offset_y = 0.0  # 目标偏移量
    current_offset_y = 0.0  # 当前偏移量
    lyrics_positions = []  # 每行歌词的位置信息
    animation_start_time = 0  # 动画开始的时间点
    animation_duration = 0.6  # 动画持续时间（秒）
    
    # 界面元素动画相关变量
    ui_animation_active = False  # 是否正在播放UI元素动画
    ui_animation_start_time = 0  # UI动画开始时间
    ui_animation_duration = 1.0  # UI动画持续时间（秒）
    album_target_x = 0  # 专辑封面目标X坐标
    album_current_x = 0  # 专辑封面当前X坐标
    controls_target_y = 0  # 控制区域目标Y坐标
    controls_current_y = 0  # 控制区域当前Y坐标
    lyrics_target_x = 0  # 歌词区域目标X坐标
    lyrics_current_x = 0  # 歌词区域当前X坐标
    # 标记是否是从切歌动画过来的
    from_song_transition = False  # 是否是从歌曲切换动画过来的
    
    # 性能监控变量
    draw_window_perf = 0  # 用于跟踪绘制窗口的性能
    fps_counter = 0  # 帧率计数器
    fps_timer = time.time()  # 帧率计时器
    actual_fps = 0  # 实际帧率
    
    # 预缓存资源
    background_path = get_background() # path of background
    background = pygame.image.load(background_path).convert() # random background - 使用convert优化
    background = pygame.transform.smoothscale(background, (WIDTH, HEIGHT))
    blurred_background = background.copy() # 初始时不需要模糊
    
    # 创建带有硬件加速的表面
    info_background = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA).convert_alpha()
    info_background.fill((0, 0, 0, 0))
    
    # Music cover - step 1. temporarily load the image
    temp_album_cover = pygame.image.load('./Resources/icons/unknown_album.png').convert_alpha()
    temp_album_cover.set_alpha(0)
    # Music Cover - step 2. ... then create a pygame.Surface ...
    album_cover = pygame.Surface(temp_album_cover.get_size(), flags=pygame.SRCALPHA).convert_alpha() #
    album_cover = pygame.transform.smoothscale(album_cover, (WIDTH / 3.4, WIDTH / 3.4))
    # the information of mp3 file
    id3 = ()   # assignment later
    
    # 预渲染文本
    music_title_text = pygame.font.Font('./Resources/fonts/Bold.OTF').render('', antialias=True, color=(255, 255, 255))
    music_title_text.set_alpha(0)
    music_artist_text = pygame.font.Font('./Resources/fonts/Bold.OTF').render('', antialias=True, color=(255, 255, 255))
    music_artist_text.set_alpha(0)
    music_pos_text = pygame.font.Font('./Resources/fonts/Medium.OTF').render('', antialias=True, color=(150, 150, 150))
    music_pos_text.set_alpha(100)
    reversed_music_pos_text = pygame.font.Font('./Resources/fonts/Medium.OTF').render('', antialias=True, color=(150, 150, 150))
    reversed_music_pos_text.set_alpha(100)
    
    # 进度条表面
    progress_bar_surface = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA).convert_alpha()
    progress_bar_surface.set_alpha(100)
    progress_bar_surface.set_colorkey((0, 0, 0))
    
    # width of progress bar, make it resizeable
    total_progress_bar_width = 0
    music_progress_width = 0
    
    # 预加载字体
    try:
        debug_font = pygame.font.SysFont('Consolas', 25)  # 尝试使用常见的等宽字体Consolas代替Cascadia Code
    except:
        debug_font = pygame.font.Font('./Resources/fonts/Medium.OTF', 25)  # 字体不存在时使用内置字体
    bold_font = pygame.font.Font('./Resources/fonts/Bold.OTF', 30)
    medium_font = pygame.font.Font('./Resources/fonts/Medium.OTF', 30)
    small_font = pygame.font.Font('./Resources/fonts/Medium.OTF', 20)
    
    # True if open debug screen (F3)
    toggle_debug_screen = False  # 默认关闭调试窗口
    debug_screen_text = debug_font.render('', antialias=True, color='white')
    clock = pygame.time.Clock()
    
    # False if click the close button
    running = True
    dt = 0
    # for animation
    background_blur_radius = 0
    lock = threading.Lock() # thread lock

def thread_it(func, *args: tuple):
    # pack functions into a thread
    t = threading.Thread(target=func, args=args) 
    t.daemon = True
    t.start()

def animations():
    
    global background, blurred_background, background_blur_radius, total_progress_bar_width
    
    while running:
        if music_busy: # if music playing....
            enter_animation()
        else:
            total_progress_bar_width = 0

            blur_out(speed=1, min_blur_radius=0)

            fade_out(info_background, speed=10, min_alpha=0)

            fade_out(album_cover, speed=50, min_alpha=0)
            
            fade_out(music_title_text, speed=30, min_alpha=0)

            fade_out(music_artist_text, speed=30, min_alpha=0)
            
            # fade_out(progress_bar_surface, speed=30, min_alpha=0)

            fade_out(music_pos_text, speed=30, min_alpha=0)

            fade_out(reversed_music_pos_text, speed=30, min_alpha=0)

def process_music():
    global music_busy, music_paused, music_pos, music_metadata, id3, music_title_text, music_title, music_artist, music_artist_text, album_name, music_pos_text, reversed_music_pos_text, music_start_time, music_paused_time, is_playing
    
    while running:
        music_busy = pygame.mixer.music.get_busy() or music_paused
        if music_busy:
            # 使用更可靠的时间差计算而不是pygame.mixer.music.get_pos()
            if music_start_time == 0:
                music_start_time = time.time()
                music_pos = 0
            else:
                # 计算从开始播放到现在的时间差
                if music_paused:
                    # 如果是暂停状态，使用暂停时的位置
                    music_pos = music_paused_time - music_start_time
                else:
                    # 正常播放状态
                    music_pos = time.time() - music_start_time
                
                # 确保不超过歌曲总长度
                if id3 and id3[4] and music_pos > id3[4]:
                    music_pos = id3[4]
                    
            music_metadata = pygame.mixer.music.get_metadata()
            paste_album_picture()

            pygame.draw.rect(album_cover, 'white', temp_album_cover.get_rect(), border_radius=int(10 / scale_factor))
            album_cover.blit(temp_album_cover, (0, 0), special_flags=pygame.BLEND_RGBA_MIN)
            # MUSIC INFO ------------------------------------------------------------------------
            music_title = id3[1]
            if music_title is None:
                music_title = id3[0]
            music_title_text = bold_font.render(music_title, antialias=True, color=(255, 255, 255))

            music_artist = id3[2]
            if music_artist is None:
                music_artist = ''
            music_artist_text = bold_font.render(music_artist, antialias=True, color=(255, 255, 255))
            album_name = id3[3]
            music_pos_text = small_font.render('{:0=2d}:{:0=2d}'.format(int(music_pos // 60), int(music_pos % 60)),
                                                 antialias=True, color=(150, 150, 150))
            if id3 and id3[4]:
                reversed_music_pos_text = small_font.render('{:0=2d}:{:0=2d}'.format(int((id3[4] - music_pos) // 60), int((id3[4] - music_pos) % 60)),
                                                     antialias=True, color=(150, 150, 150))
            else:
                reversed_music_pos_text = small_font.render('00:00', antialias=True, color=(150, 150, 150))
            
            # 更新播放状态标志
            is_playing = music_busy and not music_paused
            
            # 检查音乐是否结束，是否需要开始结束动画
            check_music_end()
        else:
            # 重置开始时间
            music_start_time = 0
            is_playing = False

def process_lyrics():
    """处理歌词并在控制台输出，同时更新当前显示的歌词索引"""
    global music_pos, parsed_lyrics, last_lyric_index, current_lyric_index, target_offset_y, current_offset_y, lyrics_positions, animation_start_time, is_big_jump, lyrics_need_update
    
    while running:
        if music_busy and parsed_lyrics:
            current_pos = music_pos
            
            # 确保lyrics_positions长度与parsed_lyrics匹配
            if len(lyrics_positions) != len(parsed_lyrics):
                # 重新初始化lyrics_positions
                lyrics_positions = []
                for i in range(len(parsed_lyrics)):
                    lyrics_positions.append({
                        'start_y': 120 + (i * 80),  # 初始位置
                        'current_y': 120 + (i * 80),  # 当前位置
                        'target_y': 120 + (i * 80),  # 目标位置
                        'animation_state': 'complete',  # 动画状态
                        'delay': 0  # 动画延迟
                    })
                lyrics_need_update = True
            
            # 找到当前时间应该显示的歌词
            for i, (time_mark, lyric) in enumerate(parsed_lyrics):
                if time_mark <= current_pos and (i == len(parsed_lyrics) - 1 or parsed_lyrics[i+1][0] > current_pos):
                    if i != last_lyric_index:
                        print(f"[{int(time_mark//60):02d}:{int(time_mark%60):02d}] {lyric}")
                        
                        # 保存每行歌词当前的位置作为起始位置
                        for j in range(len(lyrics_positions)):
                            lyrics_positions[j]['start_y'] = lyrics_positions[j]['current_y']
                        
                        # 更新索引并触发动画
                        last_lyric_index = i
                        current_lyric_index = i  # 更新当前高亮显示的歌词索引
                        
                        # 记录动画开始的时间
                        animation_start_time = time.time()
                        
                        # 计算每行歌词的目标位置
                        line_height = 80  # 增大行距，防止重叠
                        
                        # 设置顶部位置，让当前歌词在顶部而不是中间
                        top_position = 120  # 顶部位置
                        
                        # 重新计算所有歌词的目标位置
                        for j in range(len(parsed_lyrics)):
                            # 确保j不超出lyrics_positions的范围
                            if j < len(lyrics_positions):
                                # 计算相对于顶部的位置
                                relative_pos = (j - i) * line_height
                                lyrics_positions[j]['target_y'] = top_position + relative_pos
                                
                                # 根据是否是大幅跳转设置动画状态
                                if is_big_jump:
                                    # 大幅跳转时，所有歌词一起移动，没有延迟
                                    lyrics_positions[j]['animation_state'] = 'active'
                                    lyrics_positions[j]['delay'] = 0
                                else:
                                    # 正常播放时，歌词依次推动
                                    if j < i:  # 已播放的歌词(上方)
                                        lyrics_positions[j]['animation_state'] = 'waiting'
                                        lyrics_positions[j]['delay'] = (i - j) * 0.05  # 从当前行开始，向上延迟递增
                                    elif j == i:  # 当前歌词
                                        lyrics_positions[j]['animation_state'] = 'active'
                                        lyrics_positions[j]['delay'] = 0
                                    else:  # 未播放的歌词(下方)
                                        lyrics_positions[j]['animation_state'] = 'waiting'
                                        lyrics_positions[j]['delay'] = (j - i) * 0.05  # 从当前行开始，向下延迟递增
                        
                        # 通知需要更新歌词表面渲染
                        lyrics_need_update = True
                        
                        # 动画完成后重置大幅跳转标志
                        if is_big_jump:
                            is_big_jump = False
                    break
        
        time.sleep(0.1)  # 每0.1秒检查一次歌词

def ease_out_cubic(x):
    """快进缓出的立方缓动函数"""
    return 1 - pow(1 - x, 3)

def draw_window():
    '''Draw the screen.'''
    global background, blurred_background, info_background, background_blur_radius, music_title_text, music_artist_text, debug_screen_text, draw_window_perf, current_progress_width, target_progress_width, lyrics_surface, current_lyric_index, current_offset_y, target_offset_y, lyrics_positions, fps_counter, fps_timer, actual_fps, full_lyrics_surface, lyrics_area_width, lyrics_need_update, gradient_overlay, album_current_x, controls_current_y
    
    try:
        # FPS计数
        fps_counter += 1
        if time.time() - fps_timer >= 1.0:  # 每秒计算一次帧率
            actual_fps = fps_counter
            fps_counter = 0
            fps_timer = time.time()
        
        if toggle_debug_screen:
            debug_screen_text = debug_font.render(
'''Music Player by Doushabao_233
{fps} fps (目标: 120), 实际: {actual_fps}
draw_window function performance: {draw_perf_sec}s, [{draw_perf}]
background: {bg_img}
is playing? {is_playing}
Python version {python_ver}
mouse: {mouse_x} {mouse_y}
screen: {screen_width}x{screen_height}
info background alpha: {info_bg_alpha}
background blur variable: {bg_blur_var}
total progessbar width: {total_prog_bar_width}
music metadata: {music_meta}
'''.format(
                    fps=round(clock.get_fps()),
                    actual_fps=actual_fps,
                    draw_perf_sec=floor(draw_window_perf * 100000) / 100000,
                    draw_perf='█' * int(round(draw_window_perf, 2) * 150),
                    bg_img=background_path,
                    is_playing=music_busy,
                    python_ver=sys.version,
                    mouse_x=pygame.mouse.get_pos()[0],
                    mouse_y=pygame.mouse.get_pos()[1],
                    screen_width=WIDTH,
                    screen_height=HEIGHT,
                    info_bg_alpha=info_background.get_alpha(),
                    bg_blur_var=background_blur_radius,
                    total_prog_bar_width=total_progress_bar_width,
                    # music_pos=floor(music_pos * 100) / 100, music_length=floor(id3[4] * 100) / 100, playing_ratio=floor((music_pos/id3[4]) * 100),
                    music_meta=music_metadata
                    ),

                antialias=True,
                color='white',
                bgcolor=(0, 0, 0, 100)
            )
        
        # 检查是否有音乐正在播放或动画进行中
        if music_busy or album_animation_active or end_animation_active or song_transition_active:
            # 音乐播放界面或动画界面
            # 首先绘制背景
            screen.blit(blurred_background, (0, 0))
            
            # 如果有封面动画，绘制专辑动画
            if album_animation_active:
                draw_album_animation(screen)
            # 如果有歌曲切换动画，绘制切换动画
            elif song_transition_active:
                # 更新切换动画状态
                update_song_transition()
                # 绘制切换动画
                draw_song_transition(screen)
            # 否则绘制音乐播放界面
            elif music_busy:
                # 更新当前进度条宽度（实现先快后慢的动画效果）
                if target_progress_width > 0:
                    # 如果当前宽度接近目标宽度，慢慢接近
                    if abs(current_progress_width - target_progress_width) < 10:
                        current_progress_width += (target_progress_width - current_progress_width) * 0.1
                    else:
                        # 否则快速接近
                        current_progress_width += (target_progress_width - current_progress_width) * 0.3
                else:
                    # 正常播放时，进度条宽度与音乐播放位置同步
                    current_progress_width = total_progress_bar_width * (music_pos / id3[4]) if id3 and id3[4] else 0
                
                # 更新UI动画状态
                ui_animation_in_progress = update_ui_animation()
                
                # 绘制信息背景
                screen.blit(info_background, (0, 0))
                
                # 绘制专辑封面 - 始终显示在固定位置
                album_x = WIDTH / 25  # 始终使用固定位置
                screen.blit(album_cover, (album_x, WIDTH / 25))
                
                # 清除上一帧的进度条表面，避免拖影问题
                progress_bar_surface.fill((0, 0, 0, 0))
                
                # MUSIC PROGRESS BAR ----------------------------------------------------------------
                progress_bar_rect = get_progress_bar_rect()
                progress_bar_y = HEIGHT / 2 + 100 + 40 + 60  # 进度条的Y坐标
                
                # 进度条和控制按钮的Y偏移(动画中)
                controls_y_offset = controls_current_y - controls_target_y if ui_animation_active else 0
                
                # 绘制进度条背景
                pygame.draw.rect(progress_bar_surface, (150, 150, 150), 
                               pygame.Rect(WIDTH / 25, progress_bar_y + controls_y_offset, 
                                         total_progress_bar_width, 10), 
                               border_radius=10)
                
                # 绘制进度条前景（已播放部分）
                pygame.draw.rect(progress_bar_surface, (245, 245, 245), 
                               pygame.Rect(WIDTH / 25, progress_bar_y + controls_y_offset, 
                                         current_progress_width, 10), 
                               border_radius=10)
                
                # 鼠标悬停在进度条上时显示指示效果
                if is_mouse_over_progress_bar(pygame.mouse.get_pos()):
                    # 绘制一个竖直长方形指示器
                    mouse_x = pygame.mouse.get_pos()[0]
                    relative_x = min(max(mouse_x - (WIDTH / 25), 0), total_progress_bar_width)
                    
                    # 指示器坐标
                    indicator_x = WIDTH / 25 + relative_x
                    
                    # 绘制更宽更短的长方形 (仿Apple Music风格)
                    indicator_rect = pygame.Rect(indicator_x - 3, progress_bar_y - 5, 6, 20)  # 宽6，高20的竖直长方形
                    pygame.draw.rect(progress_bar_surface, (255, 255, 255), indicator_rect, border_radius=2)
                
                # 绘制播放/暂停按钮
                draw_play_pause_button(screen)
                
                # 绘制上一首按钮
                draw_prev_button(screen)
                
                # 绘制下一首按钮
                draw_next_button(screen)
                
                # 绘制循环播放按钮
                draw_loop_button(screen)
            
                info_background.fill((0, 0, 0))
                info_background.blit(music_title_text, (WIDTH / 25, HEIGHT / 2 + 100))
                music_artist_text.set_alpha(200) # must be
                info_background.blit(music_artist_text, (WIDTH / 25, HEIGHT / 2 + 100 + 40))
                info_background.blit(music_pos_text, (WIDTH / 25, HEIGHT / 2 + 100 + 40 + 60 + 10 + 5 + controls_y_offset))
                info_background.blit(reversed_music_pos_text, (WIDTH / 25 + total_progress_bar_width - reversed_music_pos_text.get_width(), HEIGHT / 2 + 100 + 40 + 60 + 10 + 5 + controls_y_offset))
                info_background.blit(progress_bar_surface, (0, 0)) # just put at 0, 0
                
                # 绘制歌词 -----------------------------------------------------------------
                if parsed_lyrics and lyrics_surfaces:
                    # 计算歌词显示区域的宽度和位置
                    current_lyrics_area_width = WIDTH - (WIDTH / 25 + album_cover.get_width() + 60)  # 歌词区域宽度 (多留20像素间距)
                    lyrics_x = WIDTH / 25 + album_cover.get_width() + 40  # 歌词区域x坐标（专辑封面右侧+20像素）
                    
                    # 检查歌词区域宽度是否变化，如果变化需要重新渲染
                    if lyrics_area_width != current_lyrics_area_width:
                        lyrics_area_width = current_lyrics_area_width
                        lyrics_need_update = True
                    
                    # 更新歌词位置动画
                    current_time = time.time()
                    elapsed_time = current_time - animation_start_time
                    animation_active = False
                    
                    # 为每行歌词更新位置
                    for i in range(len(lyrics_positions)):
                        # 获取当前行的位置信息
                        position_info = lyrics_positions[i]
                        
                        # 计算动画进度
                        animation_progress = 0
                        if position_info['animation_state'] == 'active' or position_info['animation_state'] == 'waiting':
                            animation_active = True
                            # 考虑延迟时间
                            delay = position_info['delay']
                            if elapsed_time > delay:
                                actual_time = min(animation_duration, elapsed_time - delay)
                                animation_progress = actual_time / animation_duration
                                
                                # 应用快进缓出的动画曲线
                                animation_progress = ease_out_cubic(animation_progress)
                                
                                # 如果动画完成，更新状态
                                if actual_time >= animation_duration:
                                    position_info['animation_state'] = 'complete'
                                    position_info['current_y'] = position_info['target_y']
                        
                        # 计算当前位置
                        if position_info['animation_state'] == 'complete':
                            position_info['current_y'] = position_info['target_y']
                        elif animation_progress > 0:
                            # 从起始位置向目标位置插值
                            position_info['current_y'] = position_info['start_y'] + (position_info['target_y'] - position_info['start_y']) * animation_progress
                    
                    # 如果有动画在运行，需要更新渲染
                    if animation_active:
                        lyrics_need_update = True
                    
                    # 如果需要更新，重新渲染歌词表面
                    if lyrics_need_update:
                        # 创建一个新的歌词表面
                        lyrics_display = pygame.Surface((lyrics_area_width, HEIGHT), pygame.SRCALPHA)
                        lyrics_display.fill((0, 0, 0, 0))
                        
                        # 创建一个全尺寸的歌词表面用于绘制
                        full_lyrics_surface = pygame.Surface((lyrics_area_width, HEIGHT), pygame.SRCALPHA)
                        full_lyrics_surface.fill((0, 0, 0, 0))
                        
                        # 绘制每一行歌词到全尺寸表面
                        line_height = 80  # 增大行距，与process_lyrics函数中保持一致
                        for i, surface in enumerate(lyrics_surfaces):
                            if i < len(lyrics_positions):
                                y_pos = lyrics_positions[i]['current_y']
                                
                                # 只绘制在屏幕范围内的歌词
                                if 80 <= y_pos <= HEIGHT - 30:
                                    # 确定歌词位置 - 左对齐（靠近专辑封面右侧）
                                    text_x = 0  # 从左边开始
                                    
                                    # 获取当前歌词文本
                                    lyric_text = parsed_lyrics[i][1]
                                    
                                    # 跳过空行
                                    if not lyric_text or lyric_text.isspace():
                                        continue
                                    
                                    # 检查鼠标是否悬停在此歌词上
                                    mouse_pos = pygame.mouse.get_pos()
                                    lyrics_x = WIDTH / 25 + album_cover.get_width() + 40
                                    is_hovering = is_mouse_over_lyrics(mouse_pos, lyrics_x, lyrics_area_width) and \
                                                 y_pos - 10 <= (mouse_pos[1] - lyrics_x + lyrics_area_width) <= y_pos + 40
                                    
                                    # 为当前播放的歌词使用突出显示
                                    if i == current_lyric_index:
                                        # 当前播放歌词 - 大号白色字体
                                        current_lyric_surface = bold_font.render(lyric_text, True, (255, 255, 255))
                                        
                                        # 检查是否需要换行
                                        if current_lyric_surface.get_width() > lyrics_area_width:
                                            # 如果文本太长，需要换行
                                            wrapped_lines = wrap_text(lyric_text, bold_font, lyrics_area_width - 10)
                                            
                                            # 绘制每一行换行后的文本
                                            for line_idx, line in enumerate(wrapped_lines):
                                                line_surface = bold_font.render(line, True, (255, 255, 255))
                                                full_lyrics_surface.blit(line_surface, (text_x, y_pos + line_idx * 30))
                                        else:
                                            # 文本不需要换行
                                            full_lyrics_surface.blit(current_lyric_surface, (text_x, y_pos))
                                    else:
                                        # 其他歌词 - 较淡的颜色，根据与当前歌词的距离调整透明度
                                        alpha = 255 - min(200, abs(i - current_lyric_index) * 40)
                                        
                                        # 如果鼠标悬停在此歌词上，增加亮度
                                        hover_color = (220, 220, 220) if is_hovering else (200, 200, 200)
                                        
                                        if alpha > 30:  # 确保有最小可见度
                                            # 检查是否需要换行
                                            if surface.get_width() > lyrics_area_width:
                                                # 如果文本太长，需要换行
                                                wrapped_lines = wrap_text(lyric_text, medium_font, lyrics_area_width - 10)
                                                
                                                # 绘制每一行换行后的文本
                                                for line_idx, line in enumerate(wrapped_lines):
                                                    line_surface = medium_font.render(line, True, hover_color)
                                                    line_surface.set_alpha(alpha)
                                                    full_lyrics_surface.blit(line_surface, (text_x, y_pos + line_idx * 30))
                                            else:
                                                # 文本不需要换行
                                                temp_surface = medium_font.render(lyric_text, True, hover_color)
                                                temp_surface.set_alpha(alpha)
                                                full_lyrics_surface.blit(temp_surface, (text_x, y_pos))
                        
                        # 将完整歌词表面复制到显示表面
                        lyrics_display.blit(full_lyrics_surface, (0, 0))
                        
                        # 标记歌词渲染已更新
                        lyrics_need_update = False
                    else:
                        # 创建一个新的显示表面
                        lyrics_display = pygame.Surface((lyrics_area_width, HEIGHT), pygame.SRCALPHA)
                        lyrics_display.fill((0, 0, 0, 0))
                        
                        # 使用缓存的表面
                        lyrics_display.blit(full_lyrics_surface, (0, 0))
                    
                    # 将歌词显示添加到界面 - 放在专辑封面右侧
                    screen.blit(lyrics_display, (lyrics_x, 0))
                elif parsed_lyrics:
                    # 如果有歌词但没有渲染，需要渲染歌词
                    render_lyrics()
                    lyrics_need_update = True
                    
                    # 从"暂无歌词"状态重新开始
                    if len(lyrics_positions) != len(parsed_lyrics):
                        lyrics_positions = []
                        for i in range(len(parsed_lyrics)):
                            lyrics_positions.append({
                                'start_y': 120 + (i * 80),  # 初始位置
                                'current_y': 120 + (i * 80),  # 当前位置
                                'target_y': 120 + (i * 80),  # 目标位置
                                'animation_state': 'complete',  # 动画状态
                                'delay': 0  # 动画延迟
                            })
            
            # 如果有结束动画，绘制结束动画（无论是否有音乐播放）
            if end_animation_active:
                draw_end_animation(screen)
        else:
            # 初始界面 - 显示歌曲选择
            draw_initial_screen(screen)
        
        if toggle_debug_screen: screen.blit(debug_screen_text, (10, 10))
        pygame.display.flip() # refresh screen
    except Exception as e:
        print(f"绘制出错: {e}")
        # 确保错误不会导致整个程序崩溃

# 帮助函数：将长文本按宽度分行
def wrap_text(text, font, max_width):
    words = text.split(' ')
    lines = []
    current_line = []
    
    # 对中文文本特殊处理
    if any('\u4e00' <= ch <= '\u9fff' for ch in text):
        # 中文文本按字符分割
        current_text = ""
        for char in text:
            test_text = current_text + char
            text_width = font.size(test_text)[0]
            if text_width <= max_width:
                current_text = test_text
            else:
                lines.append(current_text)
                current_text = char
        if current_text:
            lines.append(current_text)
    else:
        # 英文文本按单词分割
        for word in words:
            test_line = ' '.join(current_line + [word])
            text_width = font.size(test_line)[0]
            if text_width <= max_width:
                current_line.append(word)
            else:
                if current_line:
                    lines.append(' '.join(current_line))
                    current_line = [word]
                else:
                    # 单词太长，需要强制换行
                    lines.append(word)
                    current_line = []
        if current_line:
            lines.append(' '.join(current_line))
    
    return lines

def is_mouse_over_play_pause_btn(mouse_pos):
    """检查鼠标是否在播放/暂停按钮区域内"""
    btn_x = play_pause_btn_x + play_pause_btn_radius  # 按钮中心x坐标
    btn_y = play_pause_btn_y + play_pause_btn_radius  # 按钮中心y坐标
    
    # 计算鼠标位置到按钮中心的距离
    distance = ((mouse_pos[0] - btn_x) ** 2 + (mouse_pos[1] - btn_y) ** 2) ** 0.5
    
    # 如果距离小于按钮半径，则鼠标在按钮上
    return distance <= play_pause_btn_radius

def toggle_play_pause():
    """切换播放/暂停状态"""
    global music_busy, music_paused, music_start_time, music_paused_time, music_pos, is_playing
    
    if music_busy and not music_paused:
        # 当前正在播放，需要暂停
        pygame.mixer.music.pause()
        music_paused = True
        music_paused_time = time.time()  # 记录暂停时的时间点
        is_playing = False
    elif music_paused:
        # 当前已暂停，需要继续播放
        pygame.mixer.music.unpause()
        music_paused = False
        # 更新开始时间，考虑已经播放的时间
        music_start_time = time.time() - music_pos
        is_playing = True
    elif id3 and id3[0]:  # 有音乐文件但未播放
        # 重新开始播放
        pygame.mixer.music.rewind()
        pygame.mixer.music.play()
        music_busy = True
        music_paused = False
        music_start_time = time.time()
        music_pos = 0.0
        is_playing = True

def draw_play_pause_button(screen):
    """绘制播放/暂停按钮，Apple Music风格"""
    # 判断鼠标是否悬停在按钮上
    is_hovered = is_mouse_over_play_pause_btn(pygame.mouse.get_pos())
    
    # 按钮中心坐标
    btn_center_x = int(play_pause_btn_x + play_pause_btn_radius)
    btn_center_y = int(play_pause_btn_y + play_pause_btn_radius)
    
    # 根据播放状态绘制不同图标
    if music_busy and not music_paused:
        # 绘制暂停图标 (两条竖线)
        line_color = (245, 245, 245) if is_hovered else (255, 255, 255)  # 白色图标，悬停时稍暗
        line_width = int(play_pause_btn_radius * 0.15)  # 根据按钮大小调整线宽
        line_height = int(play_pause_btn_radius * 0.7)  # 高度为按钮半径的70%
        line_spacing = int(play_pause_btn_radius * 0.25)  # 两条线之间的间距
        
        # 左竖线
        left_line_rect = pygame.Rect(
            btn_center_x - line_spacing - line_width,
            btn_center_y - line_height // 2,
            line_width,
            line_height
        )
        
        # 右竖线
        right_line_rect = pygame.Rect(
            btn_center_x + line_spacing,
            btn_center_y - line_height // 2,
            line_width,
            line_height
        )
        
        # 绘制带圆角的暂停图标
        pygame.draw.rect(screen, line_color, left_line_rect, border_radius=line_width//2)
        pygame.draw.rect(screen, line_color, right_line_rect, border_radius=line_width//2)
    else:
        # 绘制播放图标 (三角形)
        play_color = (245, 245, 245) if is_hovered else (255, 255, 255)  # 白色图标，悬停时稍暗
        
        # 播放图标的大小，稍微大一点以保持视觉平衡
        play_size = int(play_pause_btn_radius * 0.75)
        
        # 向右偏移一点，使播放三角形视觉上更居中
        offset_x = int(play_pause_btn_radius * 0.1)
        
        # 创建一个三角形，Apple Music风格的三角形更加圆润
        triangle_points = [
            # 顶点1 (右侧)
            (btn_center_x + offset_x + play_size // 2, 
             btn_center_y),
            # 顶点2 (左上)
            (btn_center_x + offset_x - play_size // 2, 
             btn_center_y - play_size // 2),
            # 顶点3 (左下)
            (btn_center_x + offset_x - play_size // 2, 
             btn_center_y + play_size // 2)
        ]
        
        # 绘制播放三角形
        pygame.draw.polygon(screen, play_color, triangle_points)

def is_mouse_over_lyrics(mouse_pos, lyrics_area_x, lyrics_area_width):
    """检查鼠标是否在歌词区域内"""
    return (lyrics_area_x <= mouse_pos[0] <= lyrics_area_x + lyrics_area_width) and (0 <= mouse_pos[1] <= HEIGHT)

def find_lyric_under_mouse(mouse_pos, lyrics_area_x):
    """找到鼠标下方的歌词索引"""
    # 计算鼠标在歌词区域内的相对坐标
    relative_x = mouse_pos[0] - lyrics_area_x
    relative_y = mouse_pos[1]
    
    # 检查每行歌词的位置
    for i, position_info in enumerate(lyrics_positions):
        y_pos = position_info['current_y']
        
        # 歌词行的高度约为 30 像素
        lyric_height = 30
        
        # 检查鼠标是否在这行歌词上
        if y_pos - 10 <= relative_y <= y_pos + lyric_height:
            # 确保这行有有效的歌词
            if i < len(parsed_lyrics):
                return i
    
    return -1  # 没有找到匹配的歌词

def jump_to_lyric(lyric_index):
    """跳转到指定歌词的播放时间"""
    global music_pos, music_start_time, target_progress_width, current_progress_width, is_big_jump
    
    if lyric_index >= 0 and lyric_index < len(parsed_lyrics):
        # 获取选中歌词的时间
        target_time = parsed_lyrics[lyric_index][0]
        
        # 记录上一个位置，用于判断是否是大幅跳转
        old_pos = music_pos
        
        # 判断是否是大幅跳转(>=5秒)
        is_big_jump = abs(target_time - old_pos) >= 5.0
        
        # 暂停并重新开始音乐在新位置
        pygame.mixer.music.stop()
        pygame.mixer.music.play(start=target_time)
        
        # 更新显示位置和开始计时的时间点
        music_pos = target_time
        music_start_time = time.time() - target_time
        
        # 设置进度条动画的目标宽度
        target_progress_width = total_progress_bar_width * (target_time / id3[4]) if id3 and id3[4] else 0

# 歌曲库路径
MUSIC_LIBRARY_PATH = "C:/pymuic/"

# 歌曲库列表
music_library = []
album_covers_cache = {}  # 缓存专辑封面
selected_album_index = -1  # 当前选中的专辑索引
hover_album_index = -1  # 当前鼠标悬停的专辑索引
scroll_offset = 0  # 唱片列表滚动偏移量
target_scroll_offset = 0  # 目标滚动偏移量
scroll_velocity = 0  # 滚动速度
scroll_deceleration = 0.85  # 滚动减速系数
smooth_scroll_active = False  # 是否正在平滑滚动
mouse_wheel_sensitivity = 0.3  # 鼠标滚轮灵敏度
last_scroll_time = 0  # 上次滚动时间

# 主界面UI动画
main_ui_animation_active = False  # 是否正在播放主界面UI动画
main_ui_animation_start_time = 0  # 主界面UI动画开始时间
main_ui_animation_duration = 0.8  # 主界面UI动画持续时间(秒)
main_ui_album_list_y = 0  # 专辑列表当前Y坐标
main_ui_album_list_target_y = 0  # 专辑列表目标Y坐标
main_ui_albums_animated = []  # 记录每个专辑的动画状态

# 专辑选择动画相关变量
album_animation_active = False  # 是否正在播放专辑动画
album_animation_start_time = 0  # 动画开始时间
album_animation_duration = 1.5  # 动画持续时间(秒)
album_animation_surface = None  # 动画中的专辑封面
album_animation_start_rect = None  # 动画起始位置和大小
album_animation_cover_path = None  # 动画中的专辑路径
album_animation_phase = 0  # 动画阶段: 0=放大, 1=播放音乐并淡出
album_animation_music_started = False  # 标记音乐是否已开始播放

# 音乐结束动画相关变量
end_animation_active = False  # 是否正在播放结束动画
end_animation_start_time = 0  # 结束动画开始时间
end_animation_duration = 2.0  # 结束动画持续时间(秒)
end_animation_fade_in_duration = 1.0  # 淡入黑屏时间
end_animation_fade_out_duration = 1.0  # 淡出黑屏时间
end_animation_black_screen_alpha = 0  # 黑屏透明度

# 歌曲切换动画相关变量
song_transition_active = False  # 是否正在播放歌曲切换动画
song_transition_start_time = 0  # 切换动画开始时间
song_transition_duration = 1.2  # 切换动画持续时间(秒)
song_transition_old_cover = None  # 旧歌曲封面
song_transition_new_cover = None  # 新歌曲封面
song_transition_old_title = None  # 旧歌曲标题
song_transition_new_title = None  # 新歌曲标题
song_transition_old_artist = None  # 旧歌曲艺术家
song_transition_new_artist = None  # 新歌曲艺术家

def load_music_library():
    """加载音乐库中的所有歌曲"""
    global music_library
    
    # 确保音乐库目录存在
    if not os.path.exists(MUSIC_LIBRARY_PATH):
        try:
            os.makedirs(MUSIC_LIBRARY_PATH)
            print(f"已创建音乐库目录: {MUSIC_LIBRARY_PATH}")
        except:
            print(f"无法创建音乐库目录: {MUSIC_LIBRARY_PATH}")
            return
    
    # 获取目录中所有支持的音乐文件
    music_files = []
    for filename in os.listdir(MUSIC_LIBRARY_PATH):
        if filename.lower().endswith(tuple(SUPPORTED_FORMATS)):
            music_files.append(os.path.join(MUSIC_LIBRARY_PATH, filename))
    
    # 解析每个音乐文件的信息
    music_library = []
    for file_path in music_files:
        try:
            parsed_info = parse_file(file_path)
            if parsed_info:
                music_library.append({
                    'path': file_path,
                    'filename': parsed_info[0],
                    'title': parsed_info[1] or os.path.basename(file_path),
                    'artist': parsed_info[2] or "未知艺术家",
                    'album': parsed_info[3] or "未知专辑",
                    'length': parsed_info[4],
                    'cover': parsed_info[5],  # 二进制图像数据
                    'lyrics': parsed_info[6]  # 可能来自MP3标签或外部文件
                })
                
                # 预加载并缓存专辑封面
                if parsed_info[5]:  # 如果有封面
                    try:
                        img = Image.open(io.BytesIO(parsed_info[5]))
                        img = img.resize((int(WIDTH/8), int(WIDTH/8)), Image.LANCZOS)
                        album_covers_cache[file_path] = pygame.image.frombuffer(
                            img.tobytes(), img.size, img.mode).convert_alpha()
                    except:
                        # 使用默认封面
                        img = Image.open('./Resources/icons/unknown_album.png')
                        img = img.resize((int(WIDTH/8), int(WIDTH/8)), Image.LANCZOS)
                        album_covers_cache[file_path] = pygame.image.frombuffer(
                            img.tobytes(), img.size, img.mode).convert_alpha()
                else:
                    # 使用默认封面
                    img = Image.open('./Resources/icons/unknown_album.png')
                    img = img.resize((int(WIDTH/8), int(WIDTH/8)), Image.LANCZOS)
                    album_covers_cache[file_path] = pygame.image.frombuffer(
                        img.tobytes(), img.size, img.mode).convert_alpha()
        except Exception as e:
            print(f"加载歌曲出错: {file_path}, 错误: {e}")
    
    print(f"已加载 {len(music_library)} 首歌曲")

def is_mouse_over_album(mouse_pos, album_index):
    """检查鼠标是否在专辑封面上"""
    if not music_library or album_index < 0 or album_index >= len(music_library):
        return False
    
    # 计算专辑位置
    album_x = WIDTH - (WIDTH / 4) + 20  # 右侧区域起始位置
    album_y = 100 + (album_index - scroll_offset) * (WIDTH/8 + 30)  # 每个专辑的Y位置
    
    # 检查鼠标是否在专辑区域内
    return (album_x <= mouse_pos[0] <= album_x + WIDTH/8 and 
            album_y <= mouse_pos[1] <= album_y + WIDTH/8)

def update_scroll_position():
    """更新滚动位置，使用平滑滚动效果"""
    global scroll_offset, target_scroll_offset, scroll_velocity, smooth_scroll_active
    
    # 如果需要平滑滚动
    if smooth_scroll_active:
        # 计算当前位置与目标位置的差距
        scroll_distance = target_scroll_offset - scroll_offset
        
        # 如果差距很小，直接到达目标位置
        if abs(scroll_distance) < 0.01:
            scroll_offset = target_scroll_offset
            scroll_velocity = 0
            smooth_scroll_active = False
        else:
            # 更新当前滚动位置，使用平滑插值
            scroll_offset += scroll_distance * 0.2  # 逐渐接近目标位置
            
            # 应用惯性效果
            if abs(scroll_velocity) > 0:
                scroll_offset += scroll_velocity
                scroll_velocity *= scroll_deceleration  # 速度递减
                
                # 如果速度太小，停止滚动
                if abs(scroll_velocity) < 0.01:
                    scroll_velocity = 0
    
    # 确保滚动偏移量在有效范围内
    album_width = WIDTH / 6  # 专辑封面宽度
    visible_width = WIDTH - 100  # 可视区域宽度
    max_visible_albums = int(visible_width / (album_width + 30))  # 最多可见的专辑数
    max_offset = max(0, len(music_library) - max_visible_albums)
    scroll_offset = min(max(0, scroll_offset), max_offset)
    target_scroll_offset = min(max(0, target_scroll_offset), max_offset)

def draw_album_list(screen):
    """绘制右侧的专辑列表"""
    if not music_library:
        # 如果没有歌曲，显示提示信息
        no_music_text = bold_font.render("没有找到歌曲", True, (200, 200, 200))
        screen.blit(no_music_text, (WIDTH - (WIDTH / 4) + 20, 100))
        
        help_text = medium_font.render("请将音乐文件放入:", True, (180, 180, 180))
        screen.blit(help_text, (WIDTH - (WIDTH / 4) + 20, 150))
        
        path_text = small_font.render(MUSIC_LIBRARY_PATH, True, (160, 160, 160))
        screen.blit(path_text, (WIDTH - (WIDTH / 4) + 20, 190))
        return
    
    # 绘制标题
    title_text = bold_font.render("音乐库", True, (230, 230, 230))
    screen.blit(title_text, (WIDTH - (WIDTH / 4) + 20, 50))
    
    # 更新滚动位置
    update_scroll_position()
    
    # 绘制每个专辑封面
    start_index = max(0, int(scroll_offset) - 1)  # 多显示一个以避免滚动空隙
    visible_height = HEIGHT - 100  # 可视区域高度
    max_visible_albums = int(visible_height / (WIDTH/8 + 30))  # 最多可见的专辑数
    
    for i in range(start_index, min(len(music_library), start_index + max_visible_albums + 2)):  # 多渲染两个以避免滚动空隙
        # 计算位置
        album_x = WIDTH - (WIDTH / 4) + 20
        album_y = 100 + (i - scroll_offset) * (WIDTH/8 + 30)
        
        # 如果在屏幕外太远，跳过渲染以提高性能
        if album_y < -WIDTH/8 - 30 or album_y > HEIGHT + WIDTH/8:
            continue
        
        # 获取专辑信息
        album_info = music_library[i]
        
        # 绘制专辑封面
        album_cover = album_covers_cache.get(album_info['path'])
        if album_cover:
            # 根据选中和悬停状态添加效果
            if i == selected_album_index:
                # 选中的专辑显示边框
                border_rect = pygame.Rect(album_x - 5, album_y - 5, WIDTH/8 + 10, WIDTH/8 + 10)
                pygame.draw.rect(screen, (230, 230, 230), border_rect, border_radius=10)
            elif i == hover_album_index:
                # 悬停的专辑显示轻微边框
                border_rect = pygame.Rect(album_x - 3, album_y - 3, WIDTH/8 + 6, WIDTH/8 + 6)
                pygame.draw.rect(screen, (180, 180, 180), border_rect, border_radius=8)
            
            # 绘制封面圆角矩形
            album_rect = pygame.Rect(album_x, album_y, WIDTH/8, WIDTH/8)
            pygame.draw.rect(screen, (50, 50, 50), album_rect, border_radius=8)
            
            # 绘制专辑封面
            screen.blit(album_cover, (album_x, album_y))
        
        # 绘制专辑标题和艺术家
        if album_info.get('title'):
            # 裁剪过长的标题
            truncated_title = album_info['title']
            if medium_font.size(truncated_title)[0] > WIDTH/4 - 40:
                truncated_title = truncated_title[:15] + "..."
            
            title_text = medium_font.render(truncated_title, True, (210, 210, 210))
            screen.blit(title_text, (album_x + WIDTH/8 + 15, album_y + 10))
        
        if album_info.get('artist'):
            # 裁剪过长的艺术家名称
            truncated_artist = album_info['artist']
            if small_font.size(truncated_artist)[0] > WIDTH/4 - 40:
                truncated_artist = truncated_artist[:20] + "..."
            
            artist_text = small_font.render(truncated_artist, True, (170, 170, 170))
            screen.blit(artist_text, (album_x + WIDTH/8 + 15, album_y + 50))
    
    # 绘制滚动指示器
    if len(music_library) > max_visible_albums:
        # 计算滚动条位置
        scroll_height = HEIGHT - 200
        thumb_height = max(50, scroll_height * max_visible_albums / len(music_library))
        thumb_pos = 100 + (scroll_height - thumb_height) * scroll_offset / (len(music_library) - max_visible_albums)
        
        # 绘制滚动条
        scroll_x = WIDTH - 20
        pygame.draw.rect(screen, (100, 100, 100), 
                        pygame.Rect(scroll_x, 100, 5, scroll_height), 
                        border_radius=3)
        
        # 绘制滚动条滑块
        pygame.draw.rect(screen, (180, 180, 180), 
                        pygame.Rect(scroll_x, thumb_pos, 5, thumb_height), 
                        border_radius=3)

def play_selected_album():
    """播放选中的专辑"""
    global id3, parsed_lyrics, last_lyric_index, current_lyric_index, lyrics_surfaces, target_offset_y, current_offset_y, lyrics_positions, lyrics_need_update, is_big_jump, is_playing, music_paused, music_start_time, animation_start_time, target_progress_width, current_progress_width, album_animation_active, album_animation_start_time, album_animation_surface, album_animation_start_rect, album_animation_cover_path, album_animation_phase, album_animation_music_started, song_transition_active
    
    if selected_album_index >= 0 and selected_album_index < len(music_library):
        selected_album = music_library[selected_album_index]
        print(f"播放选中的专辑: {selected_album.get('title', '未知标题')}")
        
        # 加载音乐信息
        id3 = parse_file(selected_album['path'])
        
        # 如果已经播放过某首歌曲，则启动歌曲切换动画
        if music_busy and not song_transition_active:
            start_song_transition(id3)
            return
        
        # 开始专辑封面动画
        album_animation_active = True
        album_animation_start_time = time.time()
        album_animation_phase = 0  # 重置动画阶段
        album_animation_music_started = False  # 重置音乐播放标志
        
        # 获取专辑封面用于动画
        album_animation_cover_path = selected_album['path']
        album_animation_surface = album_covers_cache.get(selected_album['path']).copy()
        
        # 计算起始位置（水平排列的专辑列表中的当前位置）
        album_width = WIDTH / 6  # 与draw_horizontal_album_list中一致
        album_height = album_width
        album_x = 50 + (selected_album_index - scroll_offset) * (album_width + 30)  # 水平排列的X位置
        album_y = main_ui_album_list_y  # 使用主UI动画计算的Y位置
        album_animation_start_rect = pygame.Rect(album_x, album_y, album_width, album_height)
        
        # 解析歌词
        parsed_lyrics = parse_lyrics(id3[6])
        last_lyric_index = -1
        current_lyric_index = 0  # 默认选中第一行歌词
        lyrics_surfaces = []
        target_offset_y = 0
        current_offset_y = 0
        is_big_jump = False  # 重置大幅跳转标志
        print("\n=== 歌曲歌词 ===")
        
        # 预渲染歌词
        if parsed_lyrics:
            lyrics_surfaces = []
            lyrics_positions = []
            line_height = 80  # 增大行距，与process_lyrics函数中保持一致
            
            # 初始化每行歌词的位置信息
            for i, (_, lyric_text) in enumerate(parsed_lyrics):
                text_surface = medium_font.render(lyric_text, True, (200, 200, 200))
                lyrics_surfaces.append(text_surface)
                
                # 初始位置：第一行在顶部，其他行在下方
                initial_y = 120 + (i * line_height)  # 120是顶部位置
                    
                # 立即设置好目标位置，不使用入场动画
                target_y = initial_y
                
                lyrics_positions.append({
                    'start_y': initial_y,      # 起始位置
                    'current_y': initial_y,    # 当前位置
                    'target_y': target_y,      # 目标位置
                    'animation_state': 'complete',  # 动画状态: waiting, active, complete
                    'delay': 0                 # 动画延迟(秒)
                })
            
            # 预渲染缓存表面
            lyrics_need_update = True
        
        # 加载音乐（播放会在动画结束后开始）
        pygame.mixer.music.load(selected_album['path'])
        
        # 其他状态保持不变，等待动画结束后更新
        is_playing = False
        music_paused = False
        target_progress_width = 0
        current_progress_width = 0

        # 动画结束后会开始UI元素动画
        if not album_animation_active:
            # 如果没有专辑动画(例如直接拖放文件)，则立即开始UI动画
            start_ui_animation()

def draw_album_animation(screen):
    """绘制专辑封面动画"""
    global album_animation_active, album_animation_start_time, album_animation_surface, music_busy, music_start_time, animation_start_time, is_playing, music_paused, album_animation_phase, album_animation_music_started, parsed_lyrics, lyrics_surfaces, lyrics_positions, lyrics_need_update, total_progress_bar_width, current_progress_width, progress_bar_surface, info_background
    
    if not album_animation_active:
        return
    
    current_time = time.time()
    elapsed = current_time - album_animation_start_time
    
    # 阶段1：专辑封面放大到播放界面位置（0.8秒）
    if album_animation_phase == 0:
        progress = min(1.0, elapsed / 0.8)  # 放大阶段用0.8秒
        
        # 应用快入缓出的缓动函数
        eased_progress = ease_in_out_cubic(progress)
        
        # 计算动画中的位置和大小
        start_rect = album_animation_start_rect
        
        # 目标矩形（与播放界面中专辑封面相同的位置和大小）
        target_width = WIDTH / 3.4
        target_height = WIDTH / 3.4
        target_x = WIDTH / 25  # 与播放界面中的专辑封面X位置一致
        target_y = WIDTH / 25  # 与播放界面中的专辑封面Y位置一致
        
        # 计算当前矩形
        current_width = start_rect.width + (target_width - start_rect.width) * eased_progress
        current_height = start_rect.height + (target_height - start_rect.height) * eased_progress
        current_x = start_rect.x + (target_x - start_rect.x) * eased_progress
        current_y = start_rect.y + (target_y - start_rect.y) * eased_progress
        
        # 绘制黑色背景 - 从下方上升
        # 计算黑色背景的高度和位置
        bg_height = HEIGHT
        bg_max_y = 0  # 最终位置在屏幕顶部
        bg_start_y = HEIGHT  # 起始位置在屏幕底部
        bg_current_y = bg_start_y - (bg_start_y - bg_max_y) * eased_progress
        
        # 创建半透明黑色背景
        bg_surface = pygame.Surface((WIDTH, bg_height), pygame.SRCALPHA)
        bg_surface.fill((0, 0, 0, 150))  # 与info_background相同的透明度
        
        # 绘制黑色背景
        screen.blit(bg_surface, (0, bg_current_y))
        
        # 创建当前帧的封面动画表面 (放大版本)
        if album_animation_surface:
            try:
                scaled_cover = pygame.transform.smoothscale(album_animation_surface, (int(current_width), int(current_height)))
                
                # 绘制到屏幕
                screen.blit(scaled_cover, (current_x, current_y))
                
                # 放大阶段结束时，准备歌词动画，并切换到淡入阶段
                if progress >= 1.0:
                    album_animation_phase = 1  # 切换到下一阶段
                    
                    # 重置动画开始时间
                    album_animation_start_time = current_time
                    
                    # 准备歌词动画 - 预设歌词位置从屏幕右侧开始
                    if parsed_lyrics and len(parsed_lyrics) > 0:
                        lyrics_surfaces = []
                        lyrics_positions = []
                        line_height = 80  # 增大行距，与process_lyrics函数中保持一致
                        
                        # 初始化每行歌词的位置信息 - 从屏幕右侧开始
                        for i, (_, lyric_text) in enumerate(parsed_lyrics):
                            text_surface = medium_font.render(lyric_text, True, (200, 200, 200))
                            lyrics_surfaces.append(text_surface)
                            
                            # 初始位置：从右侧屏幕外开始，每行位置略有差异，避免整齐划一
                            initial_y = 120 + (i * line_height)
                            
                            # 目标位置：正常显示位置
                            target_y = initial_y
                            
                            # 每行歌词起始位置有意设置微小差异，让动画更自然
                            random_offset = (i % 3) * 20  # 0, 20或40像素的随机偏移
                            
                            lyrics_positions.append({
                                'start_y': initial_y,                   # Y轴起始位置
                                'current_y': initial_y,                 # Y轴当前位置
                                'target_y': target_y,                   # Y轴目标位置
                                'start_x': WIDTH + 100 + random_offset, # X轴起始位置（屏幕右侧，加随机偏移）
                                'current_x': WIDTH + 100 + random_offset, # X轴当前位置
                                'target_x': WIDTH / 25 + target_width + 40,  # X轴目标位置（专辑封面右侧）
                                'animation_state': 'waiting',           # 动画状态
                                'delay': 0.1 * i                        # 每行歌词依次延迟出现
                            })
                        
                        # 标记需要更新歌词渲染
                        lyrics_need_update = True
                    
                    # 初始化进度条动画
                    progress_bar_surface.fill((0, 0, 0, 0))
                    total_progress_bar_width = 0  # 从0开始逐渐增加到目标宽度
                    current_progress_width = 0
            
            except Exception as e:
                print(f"动画绘制错误: {e}")
                abort_animation()
    
    # 阶段2：歌词从右向左移入阶段
    else:
        # 歌词动画（0.7秒）
        progress = min(1.0, elapsed / 0.7)
        
        # 使用缓动函数
        eased_progress = ease_in_out_cubic(progress)
        
        # 绘制黑色背景 - 已完全显示
        bg_surface = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
        bg_surface.fill((0, 0, 0, 150))  # 与info_background相同的透明度
        screen.blit(bg_surface, (0, 0))
        
        # 先绘制专辑封面（已在最终位置）
        if album_animation_surface:
            try:
                # 目标大小和位置
                final_width = WIDTH / 3.4
                final_height = WIDTH / 3.4
                final_x = WIDTH / 25
                final_y = WIDTH / 25
                
                # 绘制最终大小的封面
                final_cover = pygame.transform.smoothscale(album_animation_surface, (int(final_width), int(final_height)))
                screen.blit(final_cover, (final_x, final_y))
                
                # 绘制歌曲信息和进度条动画
                if id3:
                    # 设置进度条的目标宽度 - 逐渐扩展
                    target_prog_width = album_cover.get_width()
                    total_progress_bar_width = target_prog_width * eased_progress
                    
                    # 进度条位置和大小
                    progress_bar_y = HEIGHT / 2 + 100 + 40 + 60  # 进度条的Y坐标
                    
                    # 先清除进度条表面
                    progress_bar_surface.fill((0, 0, 0, 0))
                    
                    # 绘制进度条背景 - 使用淡入效果
                    bg_alpha = int(150 * eased_progress)
                    progress_bg = pygame.Surface((total_progress_bar_width, 10), pygame.SRCALPHA)
                    progress_bg.fill((150, 150, 150, bg_alpha))
                    progress_bar_surface.blit(progress_bg, (WIDTH / 25, progress_bar_y))
                    
                    # 将进度条添加到屏幕
                    screen.blit(progress_bar_surface, (0, 0))
                
                # 更新歌词位置动画
                if parsed_lyrics and lyrics_positions:
                    animation_active = False
                    last_lyric_animated = False
                    all_lyrics_completed = True
                    
                    # 处理每行歌词的动画
                    for i, position_info in enumerate(lyrics_positions):
                        # 获取当前行的位置信息
                        delay = position_info['delay']
                        
                        # 考虑延迟时间
                        if elapsed > delay:
                            # 计算实际动画时间
                            actual_time = min(0.5, elapsed - delay)  # 每行歌词动画时间为0.5秒
                            animation_progress = actual_time / 0.5
                            
                            # 使用ease_in_out_cubic实现更顺滑的效果
                            eased_animation = ease_in_out_cubic(animation_progress)
                            
                            # 更新X轴位置 - 确保动画平滑
                            target_x = position_info['target_x']
                            start_x = position_info['start_x']
                            position_info['current_x'] = start_x + (target_x - start_x) * eased_animation
                            
                            # 检查此行歌词是否完成动画
                            if animation_progress < 1.0:
                                all_lyrics_completed = False
                            
                            # 检查最后一行歌词是否已进行动画
                            if i == len(lyrics_positions) - 1 and animation_progress >= 0.8:
                                last_lyric_animated = True
                    
                    # 如果动画进度足够并且音乐尚未开始播放，开始播放音乐
                    if (last_lyric_animated or progress >= 0.8) and not album_animation_music_started:
                        print("开始播放音乐 - 歌词动画完成")
                        play_music(selected_music_path)
                        album_animation_music_started = True
                
                # 如果没有歌词或歌词为空但动画已经进行足够长时间，也应该启动音乐
                elif progress >= 0.5 and not album_animation_music_started:
                    print("开始播放音乐 - 无歌词或动画进度足够")
                    play_music(selected_music_path)
                    album_animation_music_started = True
                
                # 绘制歌词
                if parsed_lyrics and lyrics_surfaces:
                    lyrics_area_width = WIDTH - (WIDTH / 25 + final_width + 60)
                    lyrics_display = pygame.Surface((lyrics_area_width, HEIGHT), pygame.SRCALPHA)
                    lyrics_display.fill((0, 0, 0, 0))
                    
                    # 绘制每行歌词
                    for i, surface in enumerate(lyrics_surfaces):
                        if i < len(lyrics_positions):
                            y_pos = lyrics_positions[i]['current_y']
                            x_offset = lyrics_positions[i]['current_x'] - (WIDTH / 25 + final_width + 40)
                            
                            # 只绘制接近或在屏幕内的歌词
                            if x_offset < lyrics_area_width + 100:
                                # 渐变透明度效果 - 右侧淡入
                                fade_factor = 1.0
                                
                                # 如果歌词正在从右侧进入，使用淡入效果
                                if x_offset > 0 and x_offset < 100:
                                    # 计算淡入因子：从右侧进入时逐渐变清晰
                                    fade_factor = 1.0 - (x_offset / 100)
                                    
                                    # 创建临时表面应用透明度
                                    temp_surface = surface.copy()
                                    temp_surface.set_alpha(int(255 * fade_factor))
                                    lyrics_display.blit(temp_surface, (x_offset, y_pos))
                                else:
                                    # 正常绘制已经完全进入的歌词
                                    lyrics_display.blit(surface, (x_offset, y_pos))
                    
                    # 将歌词添加到屏幕
                    screen.blit(lyrics_display, (WIDTH / 25 + final_width + 40, 0))
                
                # 动画完成，结束动画
                if progress >= 1.0 and album_animation_music_started:
                    # 检查所有歌词是否已完全到位
                    all_lyrics_in_position = True
                    if parsed_lyrics and lyrics_positions:
                        for pos_info in lyrics_positions:
                            # 检查是否有歌词尚未到达最终位置
                            if abs(pos_info['current_x'] - pos_info['target_x']) > 5:
                                all_lyrics_in_position = False
                                break
                    
                    # 确保所有歌词都已到位，并等待额外的时间让用户看到完整的画面
                    if all_lyrics_in_position and elapsed >= 0.9:  # 额外等待0.2秒
                        # 确保所有歌词完全到达最终位置
                        if parsed_lyrics and lyrics_positions:
                            for pos_info in lyrics_positions:
                                pos_info['current_x'] = pos_info['target_x']
                        
                        # 保存当前进度条宽度，确保UI动画开始时保持一致
                        current_progress_width = 0  # 设置为0，使播放进度从头开始
                        
                        # 设置总进度条宽度，确保与专辑封面宽度一致
                        total_progress_bar_width = album_cover.get_width()
                                
                        # 结束动画
                        album_animation_active = False
                        album_animation_phase = 0
                        
                        # 确保黑色背景已完全显示
                        info_background.fill((0, 0, 0, 150))
                        
                        # 动画结束后开始UI元素入场动画
                        start_ui_animation()
            
            except Exception as e:
                print(f"歌词动画错误: {e}")
                abort_animation()

def abort_animation():
    """出错时中止动画并确保音乐播放"""
    global album_animation_active, album_animation_phase, music_busy, is_playing, music_paused, music_start_time, album_animation_music_started
    global info_background, total_progress_bar_width, current_progress_width
    
    print("中止动画并启动音乐播放")
    album_animation_active = False
    album_animation_phase = 0
    album_animation_music_started = True
    
    # 确保黑色背景已完全显示
    info_background.fill((0, 0, 0, 150))
    
    # 设置进度条宽度
    if album_cover:
        total_progress_bar_width = album_cover.get_width()
        current_progress_width = 0
    
    # 确保音乐能够播放
    if not is_playing:
        try:
            pygame.mixer.music.play()
            is_playing = True
            music_paused = False
            music_start_time = time.time()
            music_busy = True
        except Exception as e:
            print(f"恢复播放音乐失败: {e}")
    
    # 开始UI动画
    start_ui_animation()

def draw_initial_screen(screen):
    """绘制初始屏幕"""
    # 绘制背景
    screen.blit(blurred_background, (0, 0))
    
    # 更新主界面UI动画
    update_main_ui_animation()
    
    # 绘制欢迎信息和提示
    welcome_text = bold_font.render("欢迎使用音乐播放器", True, (255, 255, 255))
    screen.blit(welcome_text, (WIDTH / 2 - welcome_text.get_width() / 2, HEIGHT / 3 - 50))
    
    # 设计一个更醒目的区域提示拖拽
    drop_area_width = WIDTH * 0.6
    drop_area_height = HEIGHT * 0.3
    drop_area_x = WIDTH / 2 - drop_area_width / 2
    drop_area_y = HEIGHT / 3 + 20
    
    # 绘制透明的拖拽区域
    drop_area = pygame.Surface((drop_area_width, drop_area_height), pygame.SRCALPHA)
    drop_area.fill((50, 50, 50, 80))
    pygame.draw.rect(drop_area, (200, 200, 200, 100), drop_area.get_rect(), width=2, border_radius=20)
    screen.blit(drop_area, (drop_area_x, drop_area_y))
    
    # 添加拖拽区域提示文字和图标
    hint_text = medium_font.render("将音乐文件拖放到这里", True, (220, 220, 220))
    screen.blit(hint_text, (WIDTH / 2 - hint_text.get_width() / 2, drop_area_y + drop_area_height / 2 - hint_text.get_height()))
    
    # 或者选择下方的歌曲
    or_text = medium_font.render("- 或者 -", True, (180, 180, 180))
    screen.blit(or_text, (WIDTH / 2 - or_text.get_width() / 2, drop_area_y + drop_area_height / 2 + 20))
    
    select_text = medium_font.render("从下方选择一首歌曲", True, (200, 200, 200))
    screen.blit(select_text, (WIDTH / 2 - select_text.get_width() / 2, drop_area_y + drop_area_height / 2 + 60))
    
    # 绘制底部水平排列的专辑列表
    draw_horizontal_album_list(screen)

def ease_in_out_cubic(t):
    """快入缓出的三次方缓动函数"""
    if t < 0.5:
        return 4 * t * t * t  # 前半段快速加速
    else:
        return 1 - pow(-2 * t + 2, 3) / 2  # 后半段缓慢减速

def check_music_end():
    """检查音乐是否结束，如果结束则开始结束动画"""
    global music_busy, end_animation_active, end_animation_start_time, end_animation_black_screen_alpha
    
    # 如果正在播放音乐（不包括暂停状态）
    if music_busy and not music_paused:
        # 检查音乐是否已播放完毕
        if id3 and id3[4] and music_pos >= id3[4] - 0.5:  # 给0.5秒的缓冲
            # 根据循环模式决定行为
            if is_loop_enabled:
                # 如果启用了循环播放，播放下一首
                play_next_song()
            else:
                # 常规模式，开始结束动画
                if not end_animation_active:
                    end_animation_active = True
                    end_animation_start_time = time.time()
                    end_animation_black_screen_alpha = 0

def draw_end_animation(screen):
    """绘制音乐结束时的黑屏过渡动画"""
    global end_animation_active, end_animation_start_time, end_animation_black_screen_alpha, music_busy
    
    if not end_animation_active:
        return
    
    current_time = time.time()
    elapsed = current_time - end_animation_start_time
    progress = min(1.0, elapsed / end_animation_duration)
    
    # 前半段：渐变至黑屏
    if progress <= 0.5:
        # 计算黑屏的透明度 (0-255)
        fade_in_progress = progress * 2  # 从0到1
        end_animation_black_screen_alpha = int(255 * fade_in_progress)
    # 后半段：从黑屏渐变到主界面
    else:
        # 如果刚进入后半段，停止音乐并重置状态
        if end_animation_black_screen_alpha == 255:
            # 停止音乐播放
            pygame.mixer.music.stop()
            music_busy = False
            
        # 计算黑屏的透明度 (255-0)
        fade_out_progress = (progress - 0.5) * 2  # 从0到1
        end_animation_black_screen_alpha = int(255 * (1 - fade_out_progress))
    
    # 绘制黑色半透明覆盖层
    black_overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
    black_overlay.fill((0, 0, 0, end_animation_black_screen_alpha))
    screen.blit(black_overlay, (0, 0))
    
    # 动画结束
    if progress >= 1.0:
        end_animation_active = False
        end_animation_black_screen_alpha = 0

def is_mouse_over_prev_btn(mouse_pos):
    """检查鼠标是否在上一首按钮区域内"""
    btn_x = prev_btn_x + prev_btn_radius  # 按钮中心x坐标
    btn_y = prev_btn_y + prev_btn_radius  # 按钮中心y坐标
    
    # 计算鼠标位置到按钮中心的距离
    distance = ((mouse_pos[0] - btn_x) ** 2 + (mouse_pos[1] - btn_y) ** 2) ** 0.5
    
    return distance <= prev_btn_radius

def is_mouse_over_next_btn(mouse_pos):
    """检查鼠标是否在下一首按钮区域内"""
    btn_x = next_btn_x + next_btn_radius  # 按钮中心x坐标
    btn_y = next_btn_y + next_btn_radius  # 按钮中心y坐标
    
    # 计算鼠标位置到按钮中心的距离
    distance = ((mouse_pos[0] - btn_x) ** 2 + (mouse_pos[1] - btn_y) ** 2) ** 0.5
    
    return distance <= next_btn_radius

def is_mouse_over_loop_btn(mouse_pos):
    """检查鼠标是否在循环播放按钮区域内"""
    btn_x = loop_btn_x + loop_btn_radius  # 按钮中心x坐标
    btn_y = loop_btn_y + loop_btn_radius  # 按钮中心y坐标
    
    # 计算鼠标位置到按钮中心的距离
    distance = ((mouse_pos[0] - btn_x) ** 2 + (mouse_pos[1] - btn_y) ** 2) ** 0.5
    
    return distance <= loop_btn_radius

def play_prev_song():
    """播放上一首歌"""
    global current_music_index, selected_album_index
    
    if not music_library or len(music_library) <= 1:
        return  # 没有歌曲或只有一首歌曲，无法切换
    
    if current_music_index == -1:
        # 如果没有记录当前播放的歌曲索引，则使用选中的专辑索引
        current_music_index = selected_album_index
    
    # 计算上一首歌的索引（循环到列表末尾）
    prev_index = (current_music_index - 1) % len(music_library)
    current_music_index = prev_index
    selected_album_index = prev_index
    
    # 播放选中的歌曲
    play_selected_album()

def play_next_song():
    """播放下一首歌"""
    global current_music_index, selected_album_index
    
    if not music_library or len(music_library) <= 1:
        return  # 没有歌曲或只有一首歌曲，无法切换
    
    if current_music_index == -1:
        # 如果没有记录当前播放的歌曲索引，则使用选中的专辑索引
        current_music_index = selected_album_index
    
    # 计算下一首歌的索引（循环到列表开头）
    next_index = (current_music_index + 1) % len(music_library)
    current_music_index = next_index
    selected_album_index = next_index
    
    # 播放选中的歌曲
    play_selected_album()

def toggle_loop_mode():
    """切换循环播放模式"""
    global is_loop_enabled
    is_loop_enabled = not is_loop_enabled

def draw_prev_button(screen):
    """绘制上一首按钮，Apple Music风格三角形按钮"""
    # 判断鼠标是否悬停在按钮上
    is_hovered = is_mouse_over_prev_btn(pygame.mouse.get_pos())
    
    # 按钮中心坐标
    btn_center_x = int(prev_btn_x + prev_btn_radius)
    btn_center_y = int(prev_btn_y + prev_btn_radius)
    
    # 按钮颜色，悬停时稍暗
    btn_color = (245, 245, 245) if is_hovered else (255, 255, 255)
    
    # 上一首按钮图标大小
    icon_size = int(prev_btn_radius * 0.7)
    
    # 向左偏移一点，使三角形视觉上更居中
    offset_x = int(prev_btn_radius * 0.1)
    
    # 创建左向三角形 - 上一首
    triangle_points = [
        # 左侧顶点
        (btn_center_x - offset_x - icon_size // 2, 
         btn_center_y),
        # 右上顶点
        (btn_center_x - offset_x + icon_size // 2, 
         btn_center_y - icon_size // 2),
        # 右下顶点
        (btn_center_x - offset_x + icon_size // 2, 
         btn_center_y + icon_size // 2)
    ]
    
    # 绘制三角形
    pygame.draw.polygon(screen, btn_color, triangle_points)
    
    # 左侧添加一个小竖线，完成"上一首"图标
    line_width = int(prev_btn_radius * 0.1)
    line_height = int(prev_btn_radius * 0.7)
    line_x = btn_center_x - offset_x - icon_size // 2 - line_width - 2  # 三角形左侧的小间距
    line_y = btn_center_y - line_height // 2
    
    line_rect = pygame.Rect(line_x, line_y, line_width, line_height)
    pygame.draw.rect(screen, btn_color, line_rect, border_radius=line_width//2)

def draw_next_button(screen):
    """绘制下一首按钮，Apple Music风格三角形按钮"""
    # 判断鼠标是否悬停在按钮上
    is_hovered = is_mouse_over_next_btn(pygame.mouse.get_pos())
    
    # 按钮中心坐标
    btn_center_x = int(next_btn_x + next_btn_radius)
    btn_center_y = int(next_btn_y + next_btn_radius)
    
    # 按钮颜色，悬停时稍暗
    btn_color = (245, 245, 245) if is_hovered else (255, 255, 255)
    
    # 下一首按钮图标大小
    icon_size = int(next_btn_radius * 0.7)
    
    # 向右偏移一点，使三角形视觉上更居中
    offset_x = int(next_btn_radius * 0.1)
    
    # 创建右向三角形 - 下一首
    triangle_points = [
        # 右侧顶点
        (btn_center_x + offset_x + icon_size // 2, 
         btn_center_y),
        # 左上顶点
        (btn_center_x + offset_x - icon_size // 2, 
         btn_center_y - icon_size // 2),
        # 左下顶点
        (btn_center_x + offset_x - icon_size // 2, 
         btn_center_y + icon_size // 2)
    ]
    
    # 绘制三角形
    pygame.draw.polygon(screen, btn_color, triangle_points)
    
    # 右侧添加一个小竖线，完成"下一首"图标
    line_width = int(next_btn_radius * 0.1)
    line_height = int(next_btn_radius * 0.7)
    line_x = btn_center_x + offset_x + icon_size // 2 + 2  # 三角形右侧的小间距
    line_y = btn_center_y - line_height // 2
    
    line_rect = pygame.Rect(line_x, line_y, line_width, line_height)
    pygame.draw.rect(screen, btn_color, line_rect, border_radius=line_width//2)

def draw_loop_button(screen):
    """绘制循环播放按钮，Apple Music风格循环图标"""
    # 判断鼠标是否悬停在按钮上
    is_hovered = is_mouse_over_loop_btn(pygame.mouse.get_pos())
    
    # 按钮中心坐标
    btn_center_x = int(loop_btn_x + loop_btn_radius)
    btn_center_y = int(loop_btn_y + loop_btn_radius)
    
    # 按钮颜色，根据是否启用循环模式和悬停状态决定
    if is_loop_enabled:
        # 循环模式已启用 - 使用更亮的颜色
        btn_color = (200, 250, 200) if is_hovered else (220, 255, 220)
    else:
        # 循环模式未启用 - 使用正常颜色
        btn_color = (245, 245, 245) if is_hovered else (255, 255, 255)
    
    # 循环图标大小和线宽
    icon_radius = int(loop_btn_radius * 0.6)
    line_width = int(loop_btn_radius * 0.1)
    
    # 绘制循环图标 - 一个圆形箭头
    arc_rect = pygame.Rect(
        btn_center_x - icon_radius, 
        btn_center_y - icon_radius,
        icon_radius * 2,
        icon_radius * 2
    )
    
    # 绘制圆弧 (约300度，留出一个缺口)
    start_angle = 0.5  # 弧度，约30度
    end_angle = 6.0  # 弧度，约343度
    pygame.draw.arc(screen, btn_color, arc_rect, start_angle, end_angle, line_width)
    
    # 绘制箭头尖
    arrow_size = int(loop_btn_radius * 0.25)
    arrow_x = btn_center_x + int(icon_radius * math.cos(end_angle))
    arrow_y = btn_center_y - int(icon_radius * math.sin(end_angle))
    
    arrow_points = [
        (arrow_x, arrow_y),
        (arrow_x - arrow_size, arrow_y - arrow_size // 2),
        (arrow_x - arrow_size // 2, arrow_y + arrow_size)
    ]
    
    pygame.draw.polygon(screen, btn_color, arrow_points)

def draw_control_buttons(screen):
    """绘制所有控制按钮"""
    draw_play_pause_button(screen)
    draw_prev_button(screen)
    draw_next_button(screen)
    draw_loop_button(screen)

def start_ui_animation():
    """开始UI元素入场动画"""
    global ui_animation_active, ui_animation_start_time, album_current_x, album_target_x, controls_current_y, controls_target_y, lyrics_current_x, lyrics_target_x, from_song_transition, info_background, total_progress_bar_width
    
    # 如果是从切歌动画过来的，不需要UI入场动画
    if from_song_transition:
        from_song_transition = False  # 重置标志
        return
    
    # 初始化动画状态
    ui_animation_active = True
    ui_animation_start_time = time.time()
    
    # 设置专辑封面直接在最终位置，不再从左侧飞入
    album_target_x = WIDTH / 25  # 最终位置
    album_current_x = WIDTH / 25  # 直接设置为最终位置
    
    # 设置控制区域目标位置和初始位置 - 使用更平滑的初始位置
    controls_target_y = HEIGHT / 2 + 100 + 40 + 60 + 60  # 最终位置
    controls_current_y = HEIGHT + 50  # 开始位置更靠近最终位置
    
    # 设置歌词区域目标位置和初始位置
    lyrics_target_x = WIDTH / 25 + album_cover.get_width() + 40  # 最终位置
    lyrics_current_x = lyrics_target_x  # X位置相同，但Y位置会在渲染时计算
    
    # 确保信息背景已经有正确的透明度，与动画中的黑色背景相同
    info_background.fill((0, 0, 0, 150))
    
    # 进度条在动画结束前已经有了初始宽度
    if total_progress_bar_width == 0:
        total_progress_bar_width = album_cover.get_width()  # 使用封面宽度作为进度条宽度

def update_ui_animation():
    """更新UI元素动画状态"""
    global ui_animation_active, album_current_x, album_target_x, controls_current_y, controls_target_y, lyrics_current_x, lyrics_target_x, progress_bar_surface, total_progress_bar_width
    
    if not ui_animation_active:
        return False
    
    current_time = time.time()
    elapsed = current_time - ui_animation_start_time
    progress = min(1.0, elapsed / ui_animation_duration)
    
    # 使用更平滑的缓动函数
    eased_progress = ease_in_out_cubic(progress)
    
    # 专辑封面保持在最终位置，不再有动画
    album_current_x = album_target_x
    
    # 更新控制区域位置 - 使用更平滑的缓动
    controls_current_y = controls_target_y + (HEIGHT + 50 - controls_target_y) * (1 - eased_progress)
    
    # 进度条动画 - 确保宽度已经设置正确
    if total_progress_bar_width < album_cover.get_width():
        # 如果进度条宽度尚未达到目标，则使用缓动动画增加宽度
        total_progress_bar_width = album_cover.get_width() * eased_progress
    
    # 动画结束 - 添加延迟确保动画完整
    if elapsed >= ui_animation_duration + 0.05:  # 多等待0.05秒确保完整
        ui_animation_active = False
        # 确保控制区域在正确位置
        controls_current_y = controls_target_y
        # 确保进度条宽度正确
        total_progress_bar_width = album_cover.get_width()
        return False
    
    return True

def start_song_transition(new_id3):
    """开始歌曲切换动画"""
    global song_transition_active, song_transition_start_time, song_transition_old_cover, song_transition_new_cover
    global song_transition_old_title, song_transition_new_title, song_transition_old_artist, song_transition_new_artist
    global temp_album_cover
    
    # 保存当前歌曲信息
    song_transition_old_cover = album_cover.copy()
    song_transition_old_title = music_title_text
    song_transition_old_artist = music_artist_text
    
    # 获取新歌曲信息
    # 解析新歌曲的封面
    if (new_id3[5] is None):
        img = Image.open('./Resources/icons/unknown_album.png')
    else:
        img = Image.open(io.BytesIO(new_id3[5]))
    
    for img_format in ['RGB', 'RGBA', 'RGBX', 'ARGB', 'BGRA', 'P']:
        try:
            temp_album_cover = pygame.image.frombytes(img.tobytes(), img.size, img_format).convert_alpha()
        except ValueError:
            continue
        else:
            break
    
    temp_album_cover = pygame.transform.smoothscale(temp_album_cover, (WIDTH / 3.4, WIDTH / 3.4))
    
    # 创建新歌曲封面
    song_transition_new_cover = pygame.Surface(temp_album_cover.get_size(), flags=pygame.SRCALPHA).convert_alpha()
    pygame.draw.rect(song_transition_new_cover, 'white', temp_album_cover.get_rect(), border_radius=int(10 / scale_factor))
    song_transition_new_cover.blit(temp_album_cover, (0, 0), special_flags=pygame.BLEND_RGBA_MIN)
    
    # 创建新歌曲标题文本
    music_title = new_id3[1]
    if music_title is None:
        music_title = new_id3[0]
    song_transition_new_title = bold_font.render(music_title, antialias=True, color=(255, 255, 255))
    
    # 创建新歌曲艺术家文本
    music_artist = new_id3[2]
    if music_artist is None:
        music_artist = ''
    song_transition_new_artist = bold_font.render(music_artist, antialias=True, color=(255, 255, 255))
    
    # 激活动画
    song_transition_active = True
    song_transition_start_time = time.time()
    
    # 加载新歌曲但暂不播放
    try:
        # 从音乐库获取歌曲路径
        if selected_album_index >= 0 and selected_album_index < len(music_library):
            song_path = music_library[selected_album_index]['path']
            pygame.mixer.music.load(song_path)
        else:
            print("无法加载音乐：未找到有效的歌曲索引")
    except Exception as e:
        print(f"加载音乐出错: {e}")

def update_song_transition():
    """更新歌曲切换动画状态"""
    global song_transition_active, song_transition_start_time, song_transition_duration, id3
    global music_busy, music_paused, is_playing, music_start_time, animation_start_time, parsed_lyrics, last_lyric_index, current_lyric_index, lyrics_positions
    global from_song_transition, lyrics_surfaces, lyrics_need_update, full_lyrics_surface  # 添加相关的全局变量
    
    if not song_transition_active:
        return False
    
    current_time = time.time()
    elapsed = current_time - song_transition_start_time
    progress = min(1.0, elapsed / song_transition_duration)
    
    # 动画结束
    if progress >= 1.0:
        song_transition_active = False
        
        # 设置标记，表示这是从切歌动画过来的
        from_song_transition = True
        
        # 开始播放新歌曲
        pygame.mixer.music.play()
        is_playing = True
        music_paused = False
        music_start_time = time.time()
        animation_start_time = time.time()
        music_busy = True
        
        # 解析新歌词
        parsed_lyrics = parse_lyrics(id3[6])
        last_lyric_index = -1
        current_lyric_index = 0
        
        # 初始化歌词相关数据
        lyrics_surfaces = []  # 清空歌词表面列表
        
        # 创建歌词文本表面列表
        if parsed_lyrics:
            for _, lyric_text in parsed_lyrics:
                # 确保歌词文本不会太长
                if len(lyric_text) > 50:  # 限制长度，避免太长
                    lyric_text = lyric_text[:47] + "..."
                
                # 使用中等大小字体渲染每行歌词
                text_surface = medium_font.render(lyric_text, True, (200, 200, 200))
                lyrics_surfaces.append(text_surface)
        
        # 重置歌词表面
        full_lyrics_surface = None
        
        # 初始化lyrics_positions数组，确保与parsed_lyrics长度匹配
        lyrics_positions = []
        for i in range(len(parsed_lyrics)):
            lyrics_positions.append({
                'start_y': 120 + (i * 80),  # 初始位置
                'current_y': 120 + (i * 80),  # 当前位置
                'target_y': 120 + (i * 80),  # 目标位置
                'animation_state': 'complete',  # 动画状态
                'delay': 0  # 动画延迟
            })
        
        # 标记需要更新歌词渲染
        lyrics_need_update = True
        
        # 开始UI元素入场动画 - 但会因为from_song_transition标记而被跳过
        start_ui_animation()
        
        return False
    
    return True

def draw_song_transition(screen):
    """绘制歌曲切换动画"""
    global song_transition_active, song_transition_start_time, song_transition_duration
    global song_transition_old_cover, song_transition_new_cover, song_transition_old_title, song_transition_new_title
    global song_transition_old_artist, song_transition_new_artist
    
    if not song_transition_active:
        return
    
    current_time = time.time()
    elapsed = current_time - song_transition_start_time
    progress = min(1.0, elapsed / song_transition_duration)
    
    # 应用快入缓出的缓动函数
    eased_progress = ease_in_out_cubic(progress)
    
    # 计算封面位置
    old_cover_start_x = WIDTH / 25
    old_cover_end_x = -song_transition_old_cover.get_width() - 50  # 向左移出屏幕
    old_cover_x = old_cover_start_x + (old_cover_end_x - old_cover_start_x) * eased_progress
    
    new_cover_start_x = WIDTH + 50  # 从屏幕右侧开始
    new_cover_end_x = WIDTH / 25
    new_cover_x = new_cover_start_x + (new_cover_end_x - new_cover_start_x) * eased_progress
    
    # 计算文本位置 (从上方飞入)
    old_text_start_y = HEIGHT / 2 + 100
    old_text_end_y = -100  # 向上移出屏幕
    old_text_y = old_text_start_y + (old_text_end_y - old_text_start_y) * eased_progress
    
    new_text_start_y = -100  # 从屏幕上方开始
    new_text_end_y = HEIGHT / 2 + 100
    new_text_y = new_text_start_y + (new_text_end_y - new_text_start_y) * eased_progress
    
    # 绘制旧封面 (向左移动)
    screen.blit(song_transition_old_cover, (old_cover_x, WIDTH / 25))
    
    # 绘制新封面 (从右侧移入)
    screen.blit(song_transition_new_cover, (new_cover_x, WIDTH / 25))
    
    # 绘制旧文本 (向上移动)
    screen.blit(song_transition_old_title, (WIDTH / 25, old_text_y))
    screen.blit(song_transition_old_artist, (WIDTH / 25, old_text_y + 40))
    
    # 绘制新文本 (从上方移入)
    screen.blit(song_transition_new_title, (WIDTH / 25, new_text_y))
    screen.blit(song_transition_new_artist, (WIDTH / 25, new_text_y + 40))

def update_main_ui_animation():
    """更新主界面UI动画状态"""
    global main_ui_animation_active, main_ui_album_list_y, main_ui_album_list_target_y, main_ui_albums_animated
    
    if not main_ui_animation_active:
        return False
    
    current_time = time.time()
    elapsed = current_time - main_ui_animation_start_time
    
    # 设置基本位置
    main_ui_album_list_y = main_ui_album_list_target_y
    
    # 更新每个专辑的位置
    animation_still_active = False
    for i, album_info in enumerate(main_ui_albums_animated):
        if elapsed <= album_info['delay']:
            # 动画尚未开始
            album_info['current_y'] = album_info['start_y']
            animation_still_active = True
        elif elapsed <= album_info['delay'] + main_ui_animation_duration:
            # 动画正在进行中
            album_progress = (elapsed - album_info['delay']) / main_ui_animation_duration
            eased_progress = ease_in_out_cubic(album_progress)
            album_info['current_y'] = album_info['start_y'] + (album_info['target_y'] - album_info['start_y']) * eased_progress
            animation_still_active = True
        else:
            # 动画已完成
            album_info['current_y'] = album_info['target_y']
    
    # 检查整体动画是否结束
    if not animation_still_active and elapsed >= main_ui_animation_duration + (len(main_ui_albums_animated) - 1) * 0.15:
        main_ui_animation_active = False
        return False
    
    return True

def start_main_ui_animation():
    """开始主界面UI动画"""
    global main_ui_animation_active, main_ui_animation_start_time, main_ui_album_list_y, main_ui_album_list_target_y, main_ui_albums_animated
    
    # 设置目标位置
    main_ui_album_list_target_y = HEIGHT - 220  # 底部位置，留出空间显示专辑封面
    main_ui_album_list_y = HEIGHT + 150  # 开始位置在窗口底部外
    
    # 初始化每个专辑的动画状态
    main_ui_albums_animated = []
    for i in range(len(music_library)):
        main_ui_albums_animated.append({
            'start_y': HEIGHT + 150,  # 初始位置在窗口下方
            'target_y': main_ui_album_list_target_y,  # 目标位置
            'current_y': HEIGHT + 150,  # 当前位置
            'delay': i * 0.15  # 每个专辑的动画延迟，依次出现
        })
    
    # 启动动画
    main_ui_animation_active = True
    main_ui_animation_start_time = time.time()

def is_mouse_over_horizontal_album(mouse_pos, album_index):
    """检查鼠标是否在水平排列的专辑封面上"""
    if not music_library or album_index < 0 or album_index >= len(music_library):
        return False
    
    # 计算专辑位置 - 水平排列
    album_width = WIDTH / 6  # 专辑封面宽度
    album_height = album_width  # 专辑封面高度
    album_x = 50 + (album_index - scroll_offset) * (album_width + 30)  # 每个专辑的X位置
    album_y = main_ui_album_list_y  # 专辑Y位置 - 使用动画计算的值
    
    # 检查鼠标是否在专辑区域内
    return (album_x <= mouse_pos[0] <= album_x + album_width and 
            album_y <= mouse_pos[1] <= album_y + album_height)

def draw_horizontal_album_list(screen):
    """绘制底部水平排列的专辑列表"""
    if not music_library:
        # 如果没有歌曲，显示提示信息
        no_music_text = bold_font.render("没有找到歌曲", True, (200, 200, 200))
        screen.blit(no_music_text, (WIDTH / 2 - no_music_text.get_width() / 2, main_ui_album_list_y - 50))
        
        help_text = medium_font.render("请将音乐文件放入:", True, (180, 180, 180))
        screen.blit(help_text, (WIDTH / 2 - help_text.get_width() / 2, main_ui_album_list_y))
        
        path_text = small_font.render(MUSIC_LIBRARY_PATH, True, (160, 160, 160))
        screen.blit(path_text, (WIDTH / 2 - path_text.get_width() / 2, main_ui_album_list_y + 40))
        return
    
    # 更新滚动位置
    update_scroll_position()
    
    # 绘制每个专辑封面 - 水平排列
    album_width = WIDTH / 6  # 专辑封面宽度
    album_height = album_width  # 专辑封面高度
    start_index = max(0, int(scroll_offset) - 1)  # 多显示一个以避免滚动空隙
    visible_width = WIDTH - 100  # 可视区域宽度
    max_visible_albums = int(visible_width / (album_width + 30))  # 最多可见的专辑数
    
    # 绘制音乐库标题
    title_text = bold_font.render("音乐库", True, (230, 230, 230))
    screen.blit(title_text, (50, main_ui_album_list_y - 50))
    
    for i in range(start_index, min(len(music_library), start_index + max_visible_albums + 2)):  # 多渲染两个以避免滚动空隙
        # 计算位置 - 水平排列
        album_x = 50 + (i - scroll_offset) * (album_width + 30)  # 每个专辑的X位置
        
        # 如果在动画中，使用单独的Y位置
        if main_ui_animation_active and i < len(main_ui_albums_animated):
            album_y = main_ui_albums_animated[i]['current_y']
        else:
            album_y = main_ui_album_list_y  # 使用默认位置
        
        # 如果在屏幕外太远，跳过渲染以提高性能
        if album_x < -album_width - 30 or album_x > WIDTH + album_width:
            continue
        
        # 获取专辑信息
        album_info = music_library[i]
        
        # 绘制专辑封面
        album_cover = album_covers_cache.get(album_info['path'])
        if album_cover:
            # 根据选中和悬停状态添加效果
            if i == selected_album_index:
                # 选中的专辑显示边框和阴影效果
                shadow_rect = pygame.Rect(album_x - 5, album_y - 5, album_width + 10, album_height + 10)
                pygame.draw.rect(screen, (50, 50, 50, 128), shadow_rect, border_radius=15)
                border_rect = pygame.Rect(album_x - 3, album_y - 3, album_width + 6, album_height + 6)
                pygame.draw.rect(screen, (230, 230, 230), border_rect, border_radius=12)
            elif i == hover_album_index:
                # 悬停的专辑显示轻微边框
                border_rect = pygame.Rect(album_x - 2, album_y - 2, album_width + 4, album_height + 4)
                pygame.draw.rect(screen, (180, 180, 180), border_rect, border_radius=10)
            
            # 调整专辑封面大小
            resized_cover = pygame.transform.smoothscale(album_cover, (int(album_width), int(album_height)))
            
            # 创建圆角矩形遮罩
            album_rect = pygame.Rect(album_x, album_y, album_width, album_height)
            pygame.draw.rect(screen, (50, 50, 50), album_rect, border_radius=10)
            
            # 绘制专辑封面
            screen.blit(resized_cover, (album_x, album_y))
            
            # 添加专辑信息标签(在封面下方)
            # 标题
            if album_info.get('title'):
                # 裁剪过长的标题
                truncated_title = album_info['title']
                if medium_font.size(truncated_title)[0] > album_width:
                    truncated_title = truncated_title[:12] + "..."
                
                title_text = small_font.render(truncated_title, True, (220, 220, 220))
                title_bg = pygame.Surface((title_text.get_width() + 10, title_text.get_height() + 6), pygame.SRCALPHA)
                title_bg.fill((0, 0, 0, 150))
                screen.blit(title_bg, (album_x + album_width/2 - title_text.get_width()/2 - 5, album_y + album_height - 30))
                screen.blit(title_text, (album_x + album_width/2 - title_text.get_width()/2, album_y + album_height - 27))
    
    # 绘制滚动指示器
    if len(music_library) > max_visible_albums:
        # 计算滚动条位置
        scroll_width = WIDTH - 100
        thumb_width = max(50, scroll_width * max_visible_albums / len(music_library))
        thumb_pos = 50 + (scroll_width - thumb_width) * scroll_offset / (len(music_library) - max_visible_albums)
        
        # 绘制滚动条
        scroll_y = main_ui_album_list_y + album_height + 20
        pygame.draw.rect(screen, (100, 100, 100), 
                        pygame.Rect(50, scroll_y, scroll_width, 5), 
                        border_radius=3)
        
        # 绘制滚动条滑块
        pygame.draw.rect(screen, (180, 180, 180), 
                        pygame.Rect(thumb_pos, scroll_y, thumb_width, 5), 
                        border_radius=3)

def play_music(music_path):
    """播放指定路径的音乐文件，并设置相关状态"""
    global is_playing, music_paused, music_start_time, animation_start_time, music_busy
    
    try:
        # 加载并播放音乐
        pygame.mixer.music.load(music_path)
        pygame.mixer.music.play()
        
        # 设置音乐播放状态
        is_playing = True
        music_paused = False
        music_start_time = time.time()
        animation_start_time = time.time()
        music_busy = True
        print(f"开始播放音乐: {music_path}")
    except Exception as e:
        print(f"音乐播放失败: {e}")
        # 尝试恢复状态
        is_playing = False
        music_busy = False

if __name__ == "__main__":
    try:
        # 加载音乐库
        load_music_library()
        
        # 初始化主界面UI动画
        start_main_ui_animation()
        
        thread_it(animations)
        thread_it(process_music)
        thread_it(process_lyrics)  # 启动歌词处理线程
        
        # 添加标记来跟踪进度条拖动状态
        is_dragging_progress_bar = False
        
        while running:
            for event in pygame.event.get():
                if event.type == pygame.QUIT: # quit program
                    running = False
                elif event.type == pygame.KEYDOWN and event.key == pygame.K_F3: # toggle debug screen
                    toggle_debug_screen = not toggle_debug_screen
                elif event.type == pygame.KEYDOWN and event.key == pygame.K_SPACE: # 空格键控制播放/暂停
                    if music_busy:  # 只有在有音乐时才响应空格键
                        toggle_play_pause()
                elif event.type == pygame.MOUSEBUTTONDOWN:
                    if event.button == 1:  # 左键点击
                        if music_busy and is_mouse_over_progress_bar(event.pos):
                            is_dragging_progress_bar = True
                            set_music_position(event.pos[0])
                        elif is_mouse_over_play_pause_btn(event.pos) and music_busy:
                            toggle_play_pause()
                        elif is_mouse_over_prev_btn(event.pos) and music_busy:
                            play_prev_song()
                        elif is_mouse_over_next_btn(event.pos) and music_busy:
                            play_next_song()
                        elif is_mouse_over_loop_btn(event.pos) and music_busy:
                            toggle_loop_mode()
                        elif music_busy:
                            # 检查是否点击了歌词
                            lyrics_x = WIDTH / 25 + album_cover.get_width() + 40
                            if is_mouse_over_lyrics(event.pos, lyrics_x, lyrics_area_width):
                                # 找到点击的歌词行
                                clicked_lyric_index = find_lyric_under_mouse(event.pos, lyrics_x)
                                if clicked_lyric_index >= 0:
                                    # 跳转到该歌词对应的播放位置
                                    jump_to_lyric(clicked_lyric_index)
                        else:
                            # 检查是否点击了专辑列表
                            for i in range(len(music_library)):
                                if is_mouse_over_horizontal_album(event.pos, i):
                                    selected_album_index = i
                                    play_selected_album()
                                    break
                    elif event.button == 4:  # 滚轮上滚
                        # 如果没有音乐播放，滚动专辑列表
                        if not music_busy and music_library:
                            # 记录滚动时间和速度
                            current_time = time.time()
                            time_diff = max(0.001, current_time - last_scroll_time)
                            last_scroll_time = current_time
                            
                            # 设置滚动速度和目标位置
                            scroll_velocity = -mouse_wheel_sensitivity / time_diff  # 向上滚动，速度为负
                            target_scroll_offset = max(0, target_scroll_offset - mouse_wheel_sensitivity)
                            smooth_scroll_active = True
                    elif event.button == 5:  # 滚轮下滚
                        # 如果没有音乐播放，滚动专辑列表
                        if not music_busy and music_library:
                            # 记录滚动时间和速度
                            current_time = time.time()
                            time_diff = max(0.001, current_time - last_scroll_time)
                            last_scroll_time = current_time
                            
                            # 计算最大滚动值
                            max_visible_albums = int((HEIGHT - 100) / (WIDTH/8 + 30))
                            max_offset = max(0, len(music_library) - max_visible_albums)
                            
                            # 设置滚动速度和目标位置
                            scroll_velocity = mouse_wheel_sensitivity / time_diff  # 向下滚动，速度为正
                            target_scroll_offset = min(max_offset, target_scroll_offset + mouse_wheel_sensitivity)
                            smooth_scroll_active = True
                elif event.type == pygame.DROPFILE: # catch files
                    if event.dict['file'].split('.')[-1] in SUPPORTED_FORMATS:
                        id3 = parse_file(event.dict['file'])
                        # 解析歌词
                        parsed_lyrics = parse_lyrics(id3[6])
                        last_lyric_index = -1
                        current_lyric_index = 0  # 默认选中第一行歌词
                        lyrics_surfaces = []
                        target_offset_y = 0
                        current_offset_y = 0
                        is_big_jump = False  # 重置大幅跳转标志
                        print("\n=== 歌曲歌词 ===")
                        
                        # 预渲染歌词
                        if parsed_lyrics:
                            lyrics_surfaces = []
                            lyrics_positions = []
                            line_height = 80  # 增大行距，与process_lyrics函数中保持一致
                            
                            # 初始化每行歌词的位置信息
                            for i, (_, lyric_text) in enumerate(parsed_lyrics):
                                text_surface = medium_font.render(lyric_text, True, (200, 200, 200))
                                lyrics_surfaces.append(text_surface)
                                
                                # 初始位置：第一行在顶部，其他行在下方
                                initial_y = 120 + (i * line_height)  # 120是顶部位置
                                    
                                # 立即设置好目标位置，不使用入场动画
                                target_y = initial_y
                                
                                lyrics_positions.append({
                                    'start_y': initial_y,      # 起始位置
                                    'current_y': initial_y,    # 当前位置
                                    'target_y': target_y,      # 目标位置
                                    'animation_state': 'complete',  # 动画状态: waiting, active, complete
                                    'delay': 0                 # 动画延迟(秒)
                                })
                            
                            # 预渲染缓存表面
                            lyrics_need_update = True
                        
                        pygame.mixer.music.load(event.dict['file'])
                        pygame.mixer.music.play()
                        is_playing = True
                        music_paused = False
                        music_start_time = time.time()  # 记录开始播放的时间点
                        animation_start_time = time.time()
                        target_progress_width = 0  # 重置目标进度条宽度
                        current_progress_width = 0  # 重置当前进度条宽度
                        
                        # 开始UI元素入场动画
                        start_ui_animation()
                    else:
                        print('illegal file format detected:', event.dict['file'].split('.')[-1])
                # 检测鼠标移动事件
                elif event.type == pygame.MOUSEMOTION:
                    if is_dragging_progress_bar:
                        set_music_position(event.pos[0])
                    elif music_busy:
                        # 检查鼠标是否在歌词区域上移动，需要更新渲染
                        lyrics_x = WIDTH / 25 + album_cover.get_width() + 40
                        if is_mouse_over_lyrics(event.pos, lyrics_x, lyrics_area_width):
                            # 如果有效歌词索引，则可能需要更新渲染以显示悬停效果
                            if find_lyric_under_mouse(event.pos, lyrics_x) >= 0:
                                lyrics_need_update = True
                    else:
                        # 检查鼠标是否悬停在专辑上
                        hover_found = False
                        for i in range(len(music_library)):
                            if is_mouse_over_horizontal_album(event.pos, i):
                                hover_album_index = i
                                hover_found = True
                                break
                        
                        if not hover_found:
                            hover_album_index = -1
                # 检测鼠标释放事件
                elif event.type == pygame.MOUSEBUTTONUP and event.button == 1:
                    is_dragging_progress_bar = False
                    
                # 添加鼠标拖动滚动支持
                elif event.type == pygame.MOUSEMOTION:
                    if event.buttons[0] and not music_busy:  # 左键按下且在初始界面
                        mouse_pos = pygame.mouse.get_pos()
                        # 检查是否在专辑列表区域
                        album_list_y_range = 100  # 专辑列表区域的高度范围
                        if mouse_pos[1] >= main_ui_album_list_y - album_list_y_range and mouse_pos[1] <= main_ui_album_list_y + WIDTH/6 + album_list_y_range:
                            # 计算拖动距离并转换为滚动速度
                            if hasattr(event, 'rel'):  # 确保有相对移动信息
                                rel_x, _ = event.rel
                                # 拖动效果：左拉右移，所以用负值
                                drag_factor = 0.03  # 控制拖动灵敏度
                                scroll_velocity = -rel_x * drag_factor
                                target_scroll_offset = scroll_offset - rel_x * drag_factor
                                smooth_scroll_active = True
                    
                    # 检查鼠标是否悬停在专辑上 - 水平布局
                    if not music_busy:
                        hover_found = False
                        for i in range(len(music_library)):
                            if is_mouse_over_horizontal_album(event.pos, i):
                                hover_album_index = i
                                hover_found = True
                                break
                        
                        if not hover_found:
                            hover_album_index = -1
                
            perf_start = time.perf_counter() # for debug
            draw_window()
            draw_window_perf = time.perf_counter() - perf_start
            
            # 限制帧率 - 根据实际情况动态调整
            try:
                # 尝试使用更高效的方式限制帧率
                clock.tick_busy_loop(200)  # 提高目标帧率以获得更流畅的体验
            except:
                # 回退到标准帧率限制
                clock.tick(120)
    except Exception as e:
        print(f"程序发生错误: {e}")
    finally:
        pygame.quit()