import pandas as pd
import matplotlib.pyplot as plt
import numpy as np

def create_visualizations(df):
    """
    Erstellt Visualisierungen der LoRaWAN-Daten mit verbesserter Behandlung von NaN-Werten
    """
    print("\n🎨 Visualisierungen werden erstellt...")
    print("   " + "="*50)
    
    # Filter out rows with NaN spreading_factor first
    df_filtered = df.dropna(subset=['spreading_factor']).copy()
    
    if df_filtered.empty:
        print("⚠️  Keine gültigen Daten für Visualisierungen verfügbar")
        return
    
    # 1. RSSI-Boxplot nach Spreading Factor (separate figure)
    plt.figure(figsize=(10, 6))
    
    if 'spreading_factor' in df_filtered.columns and not df_filtered['spreading_factor'].empty:
        # Get valid SF values and remove any remaining NaN
        sf_values = sorted([sf for sf in df_filtered['spreading_factor'].unique() if not pd.isna(sf)])
        
        if len(sf_values) > 0:
            rssi_by_sf = []
            valid_labels = []
            
            for sf in sf_values:
                sf_data = df_filtered[df_filtered['spreading_factor'] == sf]['rssi_dbm']
                if not sf_data.empty:
                    rssi_by_sf.append(sf_data)
                    # Handle both string ("SF7") and numeric (7) spreading factor values
                    if isinstance(sf, str) and sf.startswith('SF'):
                        valid_labels.append(sf)  # Already has SF prefix
                    else:
                        try:
                            valid_labels.append(f'SF{int(sf)}')  # Add SF prefix to numeric value
                        except (ValueError, TypeError):
                            valid_labels.append(str(sf))  # Fallback to string representation
            
            if rssi_by_sf:
                plt.boxplot(rssi_by_sf, labels=valid_labels)
                plt.xlabel('Spreading Factor')
                plt.ylabel('RSSI (dBm)')
                plt.title('RSSI-Verteilung nach Spreading Factor')
                plt.grid(True, alpha=0.3)
                plt.tight_layout()
                plt.show()
                print("   ✅ RSSI-Boxplot nach Spreading Factor erstellt")
            else:
                print("   ⚠️  Keine gültigen RSSI-Daten für Boxplot verfügbar")
        else:
            print("   ⚠️  Keine gültigen Spreading Factor Werte gefunden")
    else:
        print("   ⚠️  Spreading Factor Spalte nicht gefunden oder leer")
    
    # 2. SNR-Boxplot nach Spreading Factor (separate figure)
    plt.figure(figsize=(10, 6))
    
    if 'snr_db' in df_filtered.columns and len(sf_values) > 0:
        snr_by_sf = []
        valid_labels = []
        
        for sf in sf_values:
            sf_data = df_filtered[df_filtered['spreading_factor'] == sf]['snr_db'].dropna()
            if not sf_data.empty:
                snr_by_sf.append(sf_data)
                # Handle both string ("SF7") and numeric (7) spreading factor values
                if isinstance(sf, str) and sf.startswith('SF'):
                    valid_labels.append(sf)  # Already has SF prefix
                else:
                    try:
                        valid_labels.append(f'SF{int(sf)}')  # Add SF prefix to numeric value
                    except (ValueError, TypeError):
                        valid_labels.append(str(sf))  # Fallback to string representation
        
        if snr_by_sf:
            plt.boxplot(snr_by_sf, labels=valid_labels)
            plt.xlabel('Spreading Factor')
            plt.ylabel('SNR (dB)')
            plt.title('SNR-Verteilung nach Spreading Factor')
            plt.grid(True, alpha=0.3)
            plt.tight_layout()
            plt.show()
            print("   ✅ SNR-Boxplot nach Spreading Factor erstellt")
        else:
            print("   ⚠️  Keine gültigen SNR-Daten für Boxplot verfügbar")
    
    # 3. RSSI über Zeit (separate figure)
    plt.figure(figsize=(12, 6))
    
    if 'timestamp' in df_filtered.columns and 'rssi_dbm' in df_filtered.columns:
        try:
            # Konvertiere Zeitstempel falls nötig
            if not pd.api.types.is_datetime64_any_dtype(df_filtered['timestamp']):
                df_filtered['timestamp'] = pd.to_datetime(df_filtered['timestamp'])
            
            plt.plot(df_filtered['timestamp'], df_filtered['rssi_dbm'], 'b-', alpha=0.7, linewidth=1)
            plt.scatter(df_filtered['timestamp'], df_filtered['rssi_dbm'], c='blue', alpha=0.5, s=20)
            plt.xlabel('Zeit')
            plt.ylabel('RSSI (dBm)')
            plt.title('RSSI-Verlauf über Zeit')
            plt.grid(True, alpha=0.3)
            plt.xticks(rotation=45)
            plt.tight_layout()
            plt.show()
            print("   ✅ RSSI-Zeitverlauf erstellt")
        except Exception as e:
            print(f"   ⚠️  Fehler beim Erstellen des RSSI-Zeitverlaufs: {e}")
    
    # 4. Spreading Factor Verteilung (separate figure)
    plt.figure(figsize=(10, 6))
    
    if len(sf_values) > 0:
        sf_counts = df_filtered['spreading_factor'].value_counts().sort_index()
        
        # Create labels for the bar chart
        bar_labels = []
        for sf in sf_counts.index:
            if isinstance(sf, str) and sf.startswith('SF'):
                bar_labels.append(sf)
            else:
                try:
                    bar_labels.append(f'SF{int(sf)}')
                except (ValueError, TypeError):
                    bar_labels.append(str(sf))
        
        plt.bar(bar_labels, sf_counts.values,
                color='lightblue', edgecolor='darkblue', alpha=0.7)
        plt.xlabel('Spreading Factor')
        plt.ylabel('Anzahl Nachrichten')
        plt.title('Verteilung der Spreading Factors')
        plt.grid(True, alpha=0.3, axis='y')
        plt.tight_layout()
        plt.show()
        print("   ✅ Spreading Factor Verteilung erstellt")
    
    # 5. Statistik-Zusammenfassung
    print("\n📊 Statistik-Zusammenfassung:")
    print("   " + "="*30)
    
    if 'rssi_dbm' in df_filtered.columns:
        rssi_stats = df_filtered['rssi_dbm'].describe()
        print(f"   RSSI: Min={rssi_stats['min']:.1f}, Max={rssi_stats['max']:.1f}, Mittel={rssi_stats['mean']:.1f}")
    
    if 'snr_db' in df_filtered.columns:
        snr_stats = df_filtered['snr_db'].describe()
        print(f"   SNR:  Min={snr_stats['min']:.1f}, Max={snr_stats['max']:.1f}, Mittel={snr_stats['mean']:.1f}")
    
    if len(sf_values) > 0:
        print(f"   Spreading Factors: {sorted(sf_values)}")
        # Handle the mode calculation safely
        mode_values = df_filtered['spreading_factor'].mode()
        if not mode_values.empty:
            most_common_sf = mode_values.iloc[0]
            if isinstance(most_common_sf, str) and most_common_sf.startswith('SF'):
                print(f"   Häufigster SF: {most_common_sf}")
            else:
                try:
                    print(f"   Häufigster SF: SF{int(most_common_sf)}")
                except (ValueError, TypeError):
                    print(f"   Häufigster SF: {most_common_sf}")
    
    print(f"   Analysierte Datenpunkte: {len(df_filtered)} von {len(df)} gesamt")
    print("\n✅ Visualisierungen abgeschlossen!")

# Test the function if run directly
if __name__ == "__main__":
    # Create test data with NaN values to verify the fix
    test_data = {
        'timestamp': pd.date_range('2025-01-01', periods=10, freq='1H'),
        'rssi_dbm': np.random.uniform(-120, -60, 10),
        'snr_db': np.random.uniform(-10, 15, 10),
        'spreading_factor': [7, 8, np.nan, 9, 10, np.nan, 11, 12, 7, 8]
    }
    
    test_df = pd.DataFrame(test_data)
    print("Testing with sample data including NaN values...")
    create_visualizations(test_df)
