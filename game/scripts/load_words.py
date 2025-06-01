from game.models import WordBank
from django.db import IntegrityError

words = {
    'easy': [
        'کتاب',
        'سیاره',
        'میزان',
        'خانه',
        'شهرک',
        'برفک',
        'گنجان',
        'باران',
        'سایه',
        'مدرسه'
    ],
    'medium': [
        'مدادها',
        'کتابها',
        'پوشاک',
        'دوستان',
        'چراغان',
        'خوابید',
        'نوشته',
        'موسیقی',
        'مروارید',
        'آموزش'
    ],
    'hard': [
        'دانشگاه',
        'کامپیوتر',
        'برنامه‌نویسی',
        'مهندسی',
        'توسعه‌دهنده',
        'کتابخانه',
        'فناوری',
        'زبان‌شناسی',
        'ماشین‌آلات',
        'فرآیندها'
    ]
}


def load_words():
    for difficulty, word_list in words.items():
        for text in word_list:
            try:
                WordBank.objects.create(word=text, difficulty=difficulty)
                print(f'Added: {text} ({difficulty})')
            except IntegrityError:
                print(f'Duplicate: {text} skipped')
