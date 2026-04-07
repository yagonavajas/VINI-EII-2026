"""
Script para descargar archivos CSV desde Kaggle en carpetas organizadas
"""

import kagglehub
import os
import shutil
from typing import List, Dict, Union

OUTPUT_DIR = "./Aplicacion/Fuentes/kaggle/"

class KaggleDownloader:
    """Descargador de datasets desde Kaggle organizados por carpetas"""
    
    def __init__(self, base_output_dir):
        self.base_output_dir = base_output_dir
        os.makedirs(base_output_dir, exist_ok=True)
    
    def download_dataset(self, dataset_name: str, folder_name: str = None) -> bool:
        """Descarga un dataset y copia sus CSVs a una carpeta específica"""
        folder_name = folder_name or dataset_name.split('/')[-1]
        output_dir = os.path.join(self.base_output_dir, folder_name)
        os.makedirs(output_dir, exist_ok=True)
        
        print(f"\nDescargando: {dataset_name} -> {folder_name}/")
        
        try:
            path = kagglehub.dataset_download(dataset_name)
            csv_count = 0
            
            for root, dirs, files in os.walk(path):
                for file in files:
                    if file.endswith('.csv'):
                        src = os.path.join(root, file)
                        dst = os.path.join(output_dir, file)
                        shutil.copy2(src, dst)
                        print(f"  [OK] {file}")
                        csv_count += 1
            
            print(f"{csv_count} archivos descargados")
            return True
            
        except Exception as e:
            print(f"[ERROR] {dataset_name}: {str(e)}")
            return False
    
    def download_multiple_datasets(self, datasets: List[Union[str, Dict]]) -> Dict[str, bool]:
        """Descarga múltiples datasets"""
        results = {}
        for dataset_info in datasets:
            if isinstance(dataset_info, str):
                dataset_name = dataset_info
                folder_name = None
            else:
                dataset_name = dataset_info.get('name')
                folder_name = dataset_info.get('folder')
            
            results[dataset_name] = self.download_dataset(dataset_name, folder_name)
        return results
    
    def get_summary(self) -> Dict:
        """Obtiene resumen de datasets descargados"""
        summary = {'base_dir': os.path.abspath(self.base_output_dir), 'datasets': {}}
        
        if os.path.exists(self.base_output_dir):
            for folder_name in os.listdir(self.base_output_dir):
                folder_path = os.path.join(self.base_output_dir, folder_name)
                if os.path.isdir(folder_path):
                    csv_files = [f for f in os.listdir(folder_path) if f.endswith('.csv')]
                    total_size = sum(os.path.getsize(os.path.join(folder_path, f)) 
                                   for f in csv_files) / (1024*1024)
                    summary['datasets'][folder_name] = {
                        'files': csv_files,
                        'count': len(csv_files),
                        'size_mb': total_size
                    }
        return summary


# Datasets a descargar
DATASETS_TO_DOWNLOAD = [
    "technika148/football-database",
    {"name": "davidcariboo/player-scores", "folder": "player-scores"},
]


def main():
    downloader = KaggleDownloader(base_output_dir=OUTPUT_DIR)
    downloader.download_multiple_datasets(DATASETS_TO_DOWNLOAD)
    
    summary = downloader.get_summary()
    
    print(f"\n{'='*60}")
    print("RESUMEN FINAL")
    print(f"{'='*60}")
    print(f"Ubicacion: {summary['base_dir']}\n")
    
    total_files = total_size = 0
    for folder, info in summary['datasets'].items():
        print(f"{folder}/ - {info['count']} archivos ({info['size_mb']:.2f} MB)")
        total_files += info['count']
        total_size += info['size_mb']
    
    print(f"\nTotal: {total_files} archivos | {total_size:.2f} MB")


if __name__ == "__main__":
    main()
