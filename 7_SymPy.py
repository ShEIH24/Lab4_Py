"""
Выберите произвольную дифференцируемую и интегрируемую
функцию одной переменной. С помощью модуля symPy найдите и
отобразите ее производную и интеграл в аналитическом и
графическом виде. Напишите код для решения произвольного
нелинейного урванения и системы нелинейных уравнений.
"""
import sympy as sp
import numpy as np
import matplotlib.pyplot as plt
from sympy.plotting import plot
from matplotlib import rcParams

# Улучшаем отображение графиков
rcParams['figure.figsize'] = 12, 8
rcParams['font.size'] = 14

# Определяем символьную переменную
x = sp.Symbol('x')

# Выберем функцию: f(x) = x^3 - 4*x^2 + 5*sin(x)
f = x**3 - 4*x**2 + 5*sp.sin(x)

# 1. ДИФФЕРЕНЦИРОВАНИЕ
# Найдем производную функции
f_prime = sp.diff(f, x)

# 2. ИНТЕГРИРОВАНИЕ
# Найдем неопределенный интеграл
f_integral = sp.integrate(f, x)

# 3. ВЫВОД РЕЗУЛЬТАТОВ В АНАЛИТИЧЕСКОМ ВИДЕ
print("Исходная функция f(x):")
print(sp.pretty(f))
print("\nПроизводная функции f'(x):")
print(sp.pretty(f_prime))
print("\nНеопределенный интеграл функции:")
print(sp.pretty(f_integral))

# 4. ГРАФИЧЕСКОЕ ПРЕДСТАВЛЕНИЕ
# Преобразуем функции в численные функции для построения графиков
f_lambda = sp.lambdify(x, f, "numpy")
f_prime_lambda = sp.lambdify(x, f_prime, "numpy")
f_integral_lambda = sp.lambdify(x, f_integral, "numpy")

# Создаем массив значений x
x_vals = np.linspace(-2, 4, 1000)

# Вычисляем значения функций
f_vals = f_lambda(x_vals)
f_prime_vals = f_prime_lambda(x_vals)
f_integral_vals = f_integral_lambda(x_vals)

# Построение графиков
plt.figure(figsize=(14, 10))

# График функции
plt.subplot(3, 1, 1)
plt.plot(x_vals, f_vals, 'b-', label=r'$f(x) = x^3 - 4x^2 + 5\sin(x)$')
plt.grid(True)
plt.legend(fontsize=12)
plt.title('Исходная функция', fontsize=16)
plt.axhline(y=0, color='k', linestyle='-', alpha=0.3)
plt.axvline(x=0, color='k', linestyle='-', alpha=0.3)

# График производной
plt.subplot(3, 1, 2)
plt.plot(x_vals, f_prime_vals, 'r-', label=r'$f\'(x)$')
plt.grid(True)
plt.legend(fontsize=12)
plt.title('Производная функции', fontsize=16)
plt.axhline(y=0, color='k', linestyle='-', alpha=0.3)
plt.axvline(x=0, color='k', linestyle='-', alpha=0.3)

# График интеграла
plt.subplot(3, 1, 3)
plt.plot(x_vals, f_integral_vals, 'g-', label=r'$\int f(x) dx$')
plt.grid(True)
plt.legend(fontsize=12)
plt.title('Неопределенный интеграл функции', fontsize=16)
plt.axhline(y=0, color='k', linestyle='-', alpha=0.3)
plt.axvline(x=0, color='k', linestyle='-', alpha=0.3)

plt.tight_layout()
plt.savefig('function_analysis.png')
plt.show()

# 5. РЕШЕНИЕ НЕЛИНЕЙНОГО УРАВНЕНИЯ
print("\n\nРЕШЕНИЕ НЕЛИНЕЙНОГО УРАВНЕНИЯ")
print("===============================")

# Определим нелинейное уравнение: x^3 - 6*x^2 + 11*x - 6 = 0
eq = x**3 - 6*x**2 + 11*x - 6

print(f"Уравнение: {eq} = 0")

# Решаем уравнение
solutions = sp.solve(eq, x)
print("\nРешения:")
for i, sol in enumerate(solutions):
    print(f"x_{i+1} = {sol}")

# Проверка решений
print("\nПроверка решений:")
for i, sol in enumerate(solutions):
    result = eq.subs(x, sol)
    print(f"Подставляем x_{i+1} = {sol} в уравнение: {result}")

# 6. РЕШЕНИЕ СИСТЕМЫ НЕЛИНЕЙНЫХ УРАВНЕНИЙ
print("\n\nРЕШЕНИЕ СИСТЕМЫ НЕЛИНЕЙНЫХ УРАВНЕНИЙ")
print("=====================================")

# Определим вторую символьную переменную
y = sp.Symbol('y')

# Определим систему уравнений:
# 1. x^2 + y^2 = 10
# 2. x*y = 3
eq1 = x**2 + y**2 - 10
eq2 = x*y - 3

print("Система уравнений:")
print(f"1. {eq1} = 0  (x^2 + y^2 = 10)")
print(f"2. {eq2} = 0  (x*y = 3)")

# Решаем систему уравнений
system_solutions = sp.solve((eq1, eq2), (x, y))
print("\nРешения системы:")
for i, sol in enumerate(system_solutions):
    print(f"Решение {i+1}: x = {sol[0]}, y = {sol[1]}")

# Проверка решений
print("\nПроверка решений системы:")
for i, sol in enumerate(system_solutions):
    result1 = eq1.subs([(x, sol[0]), (y, sol[1])])
    result2 = eq2.subs([(x, sol[0]), (y, sol[1])])
    print(f"Решение {i+1}: x = {sol[0]}, y = {sol[1]}")
    print(f"Подставляем в первое уравнение: {result1}")
    print(f"Подставляем во второе уравнение: {result2}")
    print()

# Визуализация системы уравнений
plt.figure(figsize=(10, 8))
plt.title('Графическое решение системы уравнений', fontsize=16)

# Построение окружности x^2 + y^2 = 10
theta = np.linspace(0, 2*np.pi, 1000)
circle_x = np.sqrt(10) * np.cos(theta)
circle_y = np.sqrt(10) * np.sin(theta)
plt.plot(circle_x, circle_y, 'b-', label=r'$x^2 + y^2 = 10$')

# Построение гиперболы x*y = 3
xy_vals = np.linspace(-5, 5, 1000)
hyperbola_y1 = 3 / xy_vals
hyperbola_y2 = -3 / xy_vals  # отрицательная ветвь
plt.plot(xy_vals, hyperbola_y1, 'r-', label=r'$x \cdot y = 3$')
plt.plot(-xy_vals, hyperbola_y1, 'r-')

# Отметим точки пересечения
for sol in system_solutions:
    plt.plot(float(sol[0]), float(sol[1]), 'go', markersize=10)
    plt.annotate(f'({float(sol[0]):.2f}, {float(sol[1]):.2f})',
                 (float(sol[0]), float(sol[1])),
                 xytext=(10, 10),
                 textcoords='offset points')

plt.grid(True)
plt.axhline(y=0, color='k', linestyle='-', alpha=0.3)
plt.axvline(x=0, color='k', linestyle='-', alpha=0.3)
plt.xlim(-4, 4)
plt.ylim(-4, 4)
plt.legend(fontsize=12)
plt.gca().set_aspect('equal')
plt.savefig('system_solution.png')
plt.show()