# 2.3.2
![Скрин профилировщика](img/doctests.png)
![Скрин профилировщика](img/unittests.png)


# 2.3.3
## Найден метод, скорость работы которого можно увеличить на треть. Это метод удаления html тегов и нормализации пробелов в строке. Приведены три варианта исправления.
### Изначальная функция через strptime:
![Скрин профилировщика](img/date2.png)
### Функция через ручной парсинг даты, в 4 раза быстрее:
![Скрин профилировщика](img/date3.png)
### Самая быстрая функция, быстрее в 100+ раз. Оказалось, что формат даты в csv файлах позволяет сортировать даты как строки:
![Скрин профилировщика](img/date1.png)
### Код функций:
![Код](img/методы.png)