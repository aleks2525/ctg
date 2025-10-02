"""
Модуль для генерации тестовых данных FHR и UC в реальном времени
Имитирует работу с реальными датчиками КТГ
"""

import numpy as np
import random
import time
from typing import List, Dict, Tuple
from datetime import datetime, timedelta


class TestDataGenerator:
    """Генератор тестовых данных для мониторинга КТГ"""
    
    def __init__(self, sample_rate: float = 4.0):
        """
        Инициализация генератора
        
        Args:
            sample_rate: Частота дискретизации (Гц)
        """
        self.sample_rate = sample_rate
        self.dt = 1.0 / sample_rate  # Интервал между измерениями
        self.time_offset = 0.0
        self.fhr_baseline = 140.0  # Базовый ритм
        self.uc_baseline = 20.0    # Базовый тонус матки
        
        # Параметры для генерации реалистичных данных
        self.fhr_variability = 5.0  # Вариабельность FHR
        self.uc_variability = 3.0   # Вариабельность UC
        
        # Состояние для генерации паттернов
        self.acceleration_phase = 0
        self.deceleration_phase = 0
        self.contraction_phase = 0
        self.contraction_intensity = 0.0
        
        # Счетчики для статистики
        self.acceleration_count = 0
        self.deceleration_count = 0
        self.contraction_count = 0
        
    def generate_fhr_data(self, duration: float = 1.0) -> List[Dict[str, float]]:
        """
        Генерация данных FHR
        
        Args:
            duration: Длительность в секундах
            
        Returns:
            Список точек FHR с временными метками
        """
        points = []
        num_points = int(duration * self.sample_rate)
        
        for i in range(num_points):
            current_time = self.time_offset + i * self.dt
            
            # Базовый ритм с небольшими флуктуациями
            fhr_value = self.fhr_baseline + np.random.normal(0, self.fhr_variability)
            
            # Добавляем акселерации (каждые 2-3 минуты)
            if self.acceleration_phase > 0:
                fhr_value += 15 + np.random.normal(0, 3)
                self.acceleration_phase -= 1
                if self.acceleration_phase == 0:
                    self.acceleration_count += 1
            elif random.random() < 0.0005:  # Вероятность акселерации
                self.acceleration_phase = int(15 * self.sample_rate)  # 15 секунд
            
            # Добавляем децелерации (реже)
            if self.deceleration_phase > 0:
                fhr_value -= 20 + np.random.normal(0, 5)
                self.deceleration_phase -= 1
                if self.deceleration_phase == 0:
                    self.deceleration_count += 1
            elif random.random() < 0.0002:  # Вероятность децелерации
                self.deceleration_phase = int(20 * self.sample_rate)  # 20 секунд
            
            # Ограничиваем значения разумными пределами
            fhr_value = max(80, min(200, fhr_value))
            
            points.append({
                'time': current_time,
                'value': round(fhr_value, 2)
            })
        
        self.time_offset += duration
        return points
    
    def generate_uc_data(self, duration: float = 1.0) -> List[Dict[str, float]]:
        """
        Генерация данных UC (сокращения матки)
        
        Args:
            duration: Длительность в секундах
            
        Returns:
            Список точек UC с временными метками
        """
        points = []
        num_points = int(duration * self.sample_rate)
        
        for i in range(num_points):
            current_time = self.time_offset + i * self.dt
            
            # Базовый тонус с флуктуациями
            uc_value = self.uc_baseline + np.random.normal(0, self.uc_variability)
            
            # Добавляем сокращения матки
            if self.contraction_phase > 0:
                # Синусоидальная волна для сокращения
                phase = (self.contraction_phase / (30 * self.sample_rate)) * 2 * np.pi
                contraction_amplitude = self.contraction_intensity * np.sin(phase)
                uc_value += contraction_amplitude
                self.contraction_phase -= 1
                if self.contraction_phase == 0:
                    self.contraction_count += 1
            elif random.random() < 0.001:  # Вероятность сокращения
                self.contraction_phase = int(30 * self.sample_rate)  # 30 секунд
                self.contraction_intensity = random.uniform(20, 60)
            
            # Ограничиваем значения
            uc_value = max(0, min(100, uc_value))
            
            points.append({
                'time': current_time,
                'value': round(uc_value, 2)
            })
        
        return points
    
    def calculate_baseline_fhr(self, fhr_data: List[Dict[str, float]]) -> float:
        """Расчет базового ритма FHR"""
        if not fhr_data:
            return 0.0
        
        values = [point['value'] for point in fhr_data]
        # Убираем выбросы и считаем медиану
        values = sorted(values)
        n = len(values)
        if n % 2 == 0:
            return (values[n//2 - 1] + values[n//2]) / 2
        else:
            return values[n//2]
    
    def calculate_variability(self, fhr_data: List[Dict[str, float]]) -> float:
        """Расчет вариабельности FHR"""
        if not fhr_data:
            return 0.0
        
        values = [point['value'] for point in fhr_data]
        return np.std(values)
    
    def detect_accelerations(self, fhr_data: List[Dict[str, float]], baseline: float) -> int:
        """Детекция акселераций"""
        # Простая логика: считаем точки выше baseline + 15
        threshold = baseline + 15
        count = 0
        in_acceleration = False
        
        for point in fhr_data:
            if point['value'] > threshold:
                if not in_acceleration:
                    count += 1
                    in_acceleration = True
            else:
                in_acceleration = False
        
        return count
    
    def detect_decelerations(self, fhr_data: List[Dict[str, float]], baseline: float) -> int:
        """Детекция децелераций"""
        # Простая логика: считаем точки ниже baseline - 15
        threshold = baseline - 15
        count = 0
        in_deceleration = False
        
        for point in fhr_data:
            if point['value'] < threshold:
                if not in_deceleration:
                    count += 1
                    in_deceleration = True
            else:
                in_deceleration = False
        
        return count
    
    def calculate_hypoxia_risk(self, fhr_data: List[Dict[str, float]], 
                             uc_data: List[Dict[str, float]]) -> List[Dict[str, float]]:
        """
        Расчет риска гипоксии на основе FHR и UC данных
        
        Args:
            fhr_data: Данные FHR
            uc_data: Данные UC
            
        Returns:
            Список точек риска гипоксии
        """
        if not fhr_data or not uc_data:
            return []
        
        risk_points = []
        window_size = int(30 * self.sample_rate)  # 30-секундное окно
        
        for i in range(0, len(fhr_data), window_size):
            end_idx = min(i + window_size, len(fhr_data))
            fhr_window = fhr_data[i:end_idx]
            uc_window = uc_data[i:end_idx] if i < len(uc_data) else []
            
            if not fhr_window:
                continue
            
            # Расчет базовых метрик
            fhr_values = [p['value'] for p in fhr_window]
            fhr_mean = np.mean(fhr_values)
            fhr_std = np.std(fhr_values)
            
            uc_values = [p['value'] for p in uc_window] if uc_window else [0]
            uc_mean = np.mean(uc_values)
            
            # Расчет риска (упрощенная модель)
            risk = 0.0
            
            # Фактор 1: Отклонение от нормального ритма
            if fhr_mean < 110:
                risk += 0.3  # Брадикардия
            elif fhr_mean > 160:
                risk += 0.2  # Тахикардия
            
            # Фактор 2: Низкая вариабельность
            if fhr_std < 5:
                risk += 0.2
            
            # Фактор 3: Высокий тонус матки
            if uc_mean > 50:
                risk += 0.3
            
            # Фактор 4: Случайные флуктуации
            risk += random.uniform(0, 0.2)
            
            # Ограничиваем риск от 0 до 1
            risk = max(0.0, min(1.0, risk))
            
            risk_points.append({
                'time': fhr_window[0]['time'],
                'risk': round(risk, 3)
            })
        
        return risk_points
    
    def get_statistics(self) -> Dict[str, int]:
        """Получение текущей статистики"""
        return {
            'accelerations': self.acceleration_count,
            'decelerations': self.deceleration_count,
            'contractions': self.contraction_count
        }
    
    def reset(self):
        """Сброс генератора"""
        self.time_offset = 0.0
        self.acceleration_phase = 0
        self.deceleration_phase = 0
        self.contraction_phase = 0
        self.acceleration_count = 0
        self.deceleration_count = 0
        self.contraction_count = 0


# Глобальный экземпляр генератора
test_data_generator = TestDataGenerator()
