import aiofiles
import pandas as pd
from typing import Dict, List
from fastapi import UploadFile


class FileService:
    """Сервис для работы с файлами"""
    
    @staticmethod
    async def save_upload_file(file: UploadFile, file_path: str) -> Dict:
        """Сохранение загруженного файла"""
        async with aiofiles.open(file_path, 'wb') as out_file:
            content = await file.read()
            await out_file.write(content)
        
        # Анализ загруженного файла
        df = pd.read_csv(file_path)
        
        if 'time_sec' not in df.columns or 'value' not in df.columns:
            raise ValueError("CSV файл должен содержать колонки 'time_sec' и 'value'")
        
        points_count = len(df)
        duration = df['time_sec'].max() - df['time_sec'].min()
        
        return {
            "points_count": points_count,
            "duration": duration
        }
    
    @staticmethod
    def read_csv_data(file_path: str) -> List[Dict[str, float]]:
        """Чтение данных из CSV файла"""
        df = pd.read_csv(file_path)
        
        # Преобразуем в формат для графиков
        data = []
        for _, row in df.iterrows():
            data.append({
                "time": float(row['time_sec']),
                "value": float(row['value'])
            })
        
        return data

