import AnyQt


def is_qt5():
    return AnyQt.USED_API == 'pyqt5'
