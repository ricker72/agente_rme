"""Genera analysis_report.json usando el MapAnalyzer completo."""
import json
import sys
import traceback

def main():
    sys.path.insert(0, '.')
    
    try:
        from core.otbm.otbm_importer import OTBMImporter
        from core.analyzer.map_analyzer import MapAnalyzer

        importer = OTBMImporter()
        analyzer = MapAnalyzer(otbm_importer=importer)
        
        # Analizar issavi.otbm que tiene tiles, spawns, waypoints
        path = 'output/issavi.otbm'
        print(f"Analyzing {path}...")
        
        analysis = analyzer.analyze(path)
        report = analysis.to_dict()
        
        with open('analysis_report.json', 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2, ensure_ascii=False)
        
        print(f"\n=== Reporte generado: analysis_report.json ===")
        print(f"tile_count:        {analysis.tile_count}")
        print(f"item_count:        {analysis.item_count}")
        print(f"top_tiles:         {dict(sorted(analysis.tiles.items(), key=lambda x: x[1], reverse=True)[:5])}")
        print(f"top_items:         {dict(sorted(analysis.items.items(), key=lambda x: x[1], reverse=True)[:5])}")
        print(f"spawn_count:       {len(analysis.spawns)}")
        print(f"house_count:       {len(analysis.houses)}")
        print(f"waypoint_count:    {len(analysis.waypoints)}")
        print(f"floors:            {analysis.floors}")
        print(f"style:             {analysis.style}")
        print(f"map_size:          {analysis.map_size}")
        print(f"path_analysis:     {bool(analysis.path_analysis)}")
        print(f"density_analysis:  {bool(analysis.density_analysis)}")
        print(f"architecture:      {bool(analysis.architecture_analysis)}")
        
        return 0
    except Exception as e:
        print(f"ERROR: {e}")
        traceback.print_exc()
        return 1

if __name__ == '__main__':
    sys.exit(main())