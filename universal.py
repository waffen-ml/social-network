import datetime


def html(*lines):
    return ''.join(lines)


def get_today():
    today = datetime.date.today()
    weekday_s = ['Понедельник', 'Вторник',
        'Среда', 'Четверг', 'Пятница',
        'Суббота', 'Воскресенье'][today.weekday()]
    date_s = today.strftime('%d.%m.%y')
    return ', '.join([weekday_s, date_s])


def get_now():
    now = datetime.datetime.now()
    return now.strftime('%H:%M')


class MovingIndex:
    def __init__(self):
        self.i = 0
    
    def next(self):
        self.i += 1
        return self.i - 1


class IndexedArray:
    def __init__(self):
        self._keys = []
        self._values = []
        self.i = MovingIndex()
        self._iter_idx = 0

    def add(self, obj):
        idx = self.i.next()
        self._keys.append(idx)
        self._values.append(obj)
        return idx
    
    def _at(self, k):
        return self._keys.index(k)

    def remove(self, idx):
        i = self._at(idx)
        del self._keys[i]
        del self._values[i]

    def __getitem__(self, idx):
        return self._values[self._at(idx)]

    def __setitem__(self, idx, v):
        self._values[self._at(idx)] = v

    def __next__(self):
        self._iter_idx += 1
        if self._iter_idx > len(self._values):
            raise StopIteration
        return self._keys[self._iter_idx - 1]

    def __iter__(self):
        self._iter_idx = 0
        return self

    def items(self):
        return [(u, v) for u, v in zip(self._keys, self._values)]

    def keys(self):
        return self._keys
    
    def values(self):
        return self._values

    def get(self, idx, default=None):
        try:
            i = self._keys.index(idx)
            return self._values[i]
        except:
            return default

