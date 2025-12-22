# core/repository.py
"""
Repository Layer - Accès base de données SQLite
Responsabilité : UNIQUEMENT les requêtes SQL, aucune logique métier
"""
import sqlite3
from typing import Optional, List, Tuple, Dict, Any
from datetime import datetime


class Repository:
    """Couche d'accès aux données - Pure SQL, zéro logique métier"""
    
    def __init__(self, db_file: str = "data/XXpert.db"):
        self.conn = sqlite3.connect(db_file)
        self.cursor = self.conn.cursor()
        self._setup_db()
    
    def _setup_db(self):
        """Initialisation du schéma de base de données"""
        self.cursor.executescript("""
            CREATE TABLE IF NOT EXISTS seclass (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT UNIQUE NOT NULL,
                parent_id INTEGER,
                FOREIGN KEY (parent_id) REFERENCES seclass(id)
            );
            
            CREATE TABLE IF NOT EXISTS seprop (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT UNIQUE NOT NULL,
                type TEXT NOT NULL DEFAULT 'string'
            );
            
            CREATE TABLE IF NOT EXISTS seclass_prop (
                class_id INTEGER,
                prop_id INTEGER,
                PRIMARY KEY (class_id, prop_id),
                FOREIGN KEY (class_id) REFERENCES seclass(id),
                FOREIGN KEY (prop_id) REFERENCES seprop(id)
            );
            
            CREATE TABLE IF NOT EXISTS seinst (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                class_id INTEGER NOT NULL,
                UNIQUE(name, class_id),
                FOREIGN KEY (class_id) REFERENCES seclass(id)
            );
            
            CREATE TABLE IF NOT EXISTS seinst_value (
                inst_id INTEGER,
                prop_id INTEGER,
                value TEXT,
                PRIMARY KEY (inst_id, prop_id),
                FOREIGN KEY (inst_id) REFERENCES seinst(id),
                FOREIGN KEY (prop_id) REFERENCES seprop(id)
            );
            
            CREATE TABLE IF NOT EXISTS seprop_stats (
                class_id INTEGER,
                prop_id INTEGER,
                instance_count INTEGER DEFAULT 0,
                min_value REAL,
                max_value REAL,
                mean_value REAL,
                median_value REAL,
                std_dev REAL,
                updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                PRIMARY KEY (class_id, prop_id),
                FOREIGN KEY (class_id) REFERENCES seclass(id),
                FOREIGN KEY (prop_id) REFERENCES seprop(id)
            );
            
            CREATE TABLE IF NOT EXISTS seprop_manual_thresholds (
                class_id INTEGER,
                prop_id INTEGER,
                ll REAL,
                l REAL,
                h REAL,
                hh REAL,
                PRIMARY KEY (class_id, prop_id),
                FOREIGN KEY (class_id) REFERENCES seclass(id),
                FOREIGN KEY (prop_id) REFERENCES seprop(id)
            );
            
            CREATE TABLE IF NOT EXISTS se_users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL,
                role TEXT DEFAULT 'user',
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP
            );
            
            CREATE TABLE IF NOT EXISTS se_submissions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                description TEXT,
                changes_json TEXT,
                status TEXT DEFAULT 'pending',
                validated_by INTEGER,
                validated_at DATETIME,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES se_users(id),
                FOREIGN KEY (validated_by) REFERENCES se_users(id)
            );

            CREATE TABLE IF NOT EXISTS se_events (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                event_type TEXT NOT NULL,
                source TEXT NOT NULL,
                entity TEXT,
                payload TEXT,  # JSON
                severity TEXT DEFAULT 'info',
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
            );

        """)
        self.conn.commit()
        
        # Données initiales (classe Animal + admin)
        self._init_default_data()
    
    def _init_default_data(self):
        """Initialise les données par défaut si besoin"""
        # Classe Animal si absente
        self.cursor.execute("SELECT COUNT(*) FROM seclass WHERE name = 'Animal'")
        if self.cursor.fetchone()[0] == 0:
            self.cursor.execute("INSERT INTO seclass (name) VALUES ('Animal')")
        
        # Admin par défaut
        self.cursor.execute("SELECT COUNT(*) FROM se_users WHERE username = 'admin'")
        if self.cursor.fetchone()[0] == 0:
            self.cursor.execute("INSERT INTO se_users (username, role) VALUES ('admin', 'admin')")
        
        self.conn.commit()
    
    # ========== CLASSES ==========
    
    def get_class_id(self, name: str) -> Optional[int]:
        """Récupère l'ID d'une classe par son nom (insensible à la casse)"""
        self.cursor.execute("SELECT id FROM seclass WHERE LOWER(name) = LOWER(?)", (name,))
        row = self.cursor.fetchone()
        return row[0] if row else None
    
    def get_all_class_names(self) -> List[str]:
        """Liste tous les noms de classes"""
        self.cursor.execute("SELECT name FROM seclass ORDER BY name")
        return [row[0] for row in self.cursor.fetchall()]

#----------------------------------------------------------------------------------
    """Insère une nouvelle classe, retourne son ID on  a repris e code grok dans database"""

    """
    def insert_class(self, name: str, parent_id: Optional[int] = None) -> int:
        
        self.cursor.execute(
            "INSERT INTO seclass (name, parent_id) VALUES (?, ?)",
            (name, parent_id)
        )
        self.conn.commit()
        return self.cursor.lastrowid
        # self.store_event(event)
    """
#----------------------------------------------------------------------------------

    def add_class(self, name, parent=None):
        # name = name.strip()
        name = name.strip().capitalize()  # Première lettre majuscule

        if not name:
            console.print("[red]Le nom de la classe ne peut pas être vide[/]")
            return False

        if self.get_class_id(name):
            console.print(f"[red]Classe '{name}' existe déjà[/]")
            return False
        parent_id = self.get_class_id(parent) if parent else None
        self.cursor.execute("INSERT INTO seclass (name, parent_id) VALUES (?, ?)", (name, parent_id))
        self.commit()
        console.print(Panel(f"Classe [green]'{name}'[/] créée", style="green"))

        event = Event("class_added", "database", entity=name)
        return True, event  # return True, Event("class_added", "database", entity=name)  # Return tuple (success, event)
        self.store_event(event)
#--------------------------------------------------------------------------------

    def get_class_hierarchy(self) -> List[Tuple[int, str, Optional[int], int]]:
        """Retourne la hiérarchie complète (id, name, parent_id, level)"""
        self.cursor.execute("""
            WITH RECURSIVE tree(id, name, parent_id, level) AS (
                SELECT id, name, parent_id, 0 FROM seclass WHERE parent_id IS NULL
                UNION ALL
                SELECT c.id, c.name, c.parent_id, t.level+1 
                FROM seclass c JOIN tree t ON c.parent_id = t.id
            )
            SELECT id, name, parent_id, level FROM tree ORDER BY level, name
        """)
        return self.cursor.fetchall()
    
    # ========== PROPRIÉTÉS ==========
    
    def get_property_id(self, name: str) -> Optional[int]:
        """Récupère l'ID d'une propriété par son nom"""
        self.cursor.execute("SELECT id FROM seprop WHERE LOWER(name) = LOWER(?)", (name,))
        row = self.cursor.fetchone()
        return row[0] if row else None
    
    def get_all_property_names(self) -> List[str]:
        """Liste toutes les propriétés"""
        self.cursor.execute("SELECT name FROM seprop ORDER BY name")
        return [row[0] for row in self.cursor.fetchall()]
    
    def get_property_type(self, prop_id: int) -> Optional[str]:
        """Récupère le type d'une propriété"""
        self.cursor.execute("SELECT type FROM seprop WHERE id = ?", (prop_id,))
        row = self.cursor.fetchone()
        return row[0] if row else None
    
    def insert_property(self, name: str, ptype: str = "string") -> int:
        """Insère une nouvelle propriété"""
        self.cursor.execute(
            "INSERT INTO seprop (name, type) VALUES (?, ?)",
            (name, ptype)
        )
        self.conn.commit()
        return self.cursor.lastrowid
    
    def link_property_to_class(self, class_id: int, prop_id: int) -> bool:
        """Lie une propriété à une classe (retourne False si déjà liée)"""
        try:
            self.cursor.execute(
                "INSERT INTO seclass_prop (class_id, prop_id) VALUES (?, ?)",
                (class_id, prop_id)
            )
            self.conn.commit()
            return True
        except sqlite3.IntegrityError:
            return False  # Déjà lié
    
    def get_properties_for_class(self, class_id: int) -> List[Tuple[int, str, str]]:
        """Retourne les propriétés héritées (id, name, type) - avec héritage"""
        props = []
        visited = set()
        current = class_id
        
        while current:
            self.cursor.execute("""
                SELECT p.id, p.name, p.type 
                FROM seprop p 
                JOIN seclass_prop cp ON p.id = cp.prop_id 
                WHERE cp.class_id = ?
            """, (current,))
            
            for row in self.cursor.fetchall():
                if row[0] not in visited:
                    props.append(row)
                    visited.add(row[0])
            
            # Parent
            self.cursor.execute("SELECT parent_id FROM seclass WHERE id = ?", (current,))
            row = self.cursor.fetchone()
            current = row[0] if row else None
        
        return props
    
    # ========== INSTANCES ==========
    
    def get_instance_id(self, name: str, class_id: int) -> Optional[int]:
        """Récupère l'ID d'une instance"""
        self.cursor.execute(
            "SELECT id FROM seinst WHERE LOWER(name) = LOWER(?) AND class_id = ?",
            (name, class_id)
        )
        row = self.cursor.fetchone()
        return row[0] if row else None
    
    def insert_instance(self, name: str, class_id: int) -> int:
        """Insère une nouvelle instance"""
        self.cursor.execute(
            "INSERT INTO seinst (name, class_id) VALUES (?, ?)",
            (name, class_id)
        )
        self.conn.commit()
        return self.cursor.lastrowid
    
    def get_all_instances(self, class_id: int) -> List[str]:
        """Liste toutes les instances d'une classe"""
        self.cursor.execute(
            "SELECT name FROM seinst WHERE class_id = ? ORDER BY name",
            (class_id,)
        )
        return [row[0] for row in self.cursor.fetchall()]
    
    # ========== VALEURS ==========
    
    def get_instance_value(self, inst_id: int, prop_id: int) -> Optional[str]:
        """Récupère la valeur brute (string) d'une propriété pour une instance"""
        self.cursor.execute(
            "SELECT value FROM seinst_value WHERE inst_id = ? AND prop_id = ?",
            (inst_id, prop_id)
        )
        row = self.cursor.fetchone()
        return row[0] if row else None
    
    def upsert_instance_value(self, inst_id: int, prop_id: int, value: Optional[str]):
        """Insert ou update une valeur"""
        self.cursor.execute("""
            INSERT INTO seinst_value (inst_id, prop_id, value)
            VALUES (?, ?, ?)
            ON CONFLICT(inst_id, prop_id) DO UPDATE SET value = excluded.value
        """, (inst_id, prop_id, value))
        self.conn.commit()
    
    # ========== STATISTIQUES ==========
    
    def get_stats(self, class_id: int, prop_id: int) -> Optional[Dict[str, Any]]:
        """Récupère les statistiques pour une propriété numérique"""
        self.cursor.execute("""
            SELECT instance_count, min_value, max_value, mean_value, median_value, std_dev
            FROM seprop_stats
            WHERE class_id = ? AND prop_id = ?
        """, (class_id, prop_id))
        row = self.cursor.fetchone()
        if row:
            return {
                "count": row[0],
                "min": row[1],
                "max": row[2],
                "mean": row[3],
                "median": row[4],
                "std_dev": row[5]
            }
        return None
    
    def upsert_stats(self, class_id: int, prop_id: int, stats: Dict[str, Any]):
        """Insert ou update des statistiques"""
        self.cursor.execute("""
            INSERT INTO seprop_stats 
                (class_id, prop_id, instance_count, min_value, max_value, mean_value, median_value, std_dev)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(class_id, prop_id) DO UPDATE SET
                instance_count = excluded.instance_count,
                min_value = excluded.min_value,
                max_value = excluded.max_value,
                mean_value = excluded.mean_value,
                median_value = excluded.median_value,
                std_dev = excluded.std_dev,
                updated_at = CURRENT_TIMESTAMP
        """, (
            class_id, prop_id,
            stats.get("count", 0),
            stats.get("min"),
            stats.get("max"),
            stats.get("mean"),
            stats.get("median"),
            stats.get("std_dev")
        ))
        self.conn.commit()
    
    def get_all_numeric_values(self, class_id: int, prop_id: int) -> List[float]:
        """Récupère toutes les valeurs numériques pour calcul stats"""
        self.cursor.execute("""
            SELECT v.value 
            FROM seinst_value v
            JOIN seinst i ON v.inst_id = i.id
            WHERE i.class_id = ? AND v.prop_id = ? AND v.value IS NOT NULL
        """, (class_id, prop_id))
        
        values = []
        for row in self.cursor.fetchall():
            try:
                values.append(float(row[0]))
            except (ValueError, TypeError):
                pass
        return values
    
    # ========== SEUILS MANUELS ==========
    
    def get_manual_thresholds(self, class_id: int, prop_id: int) -> Optional[Dict[str, Optional[float]]]:
        """Récupère les seuils manuels"""
        self.cursor.execute(
            "SELECT ll, l, h, hh FROM seprop_manual_thresholds WHERE class_id = ? AND prop_id = ?",
            (class_id, prop_id)
        )
        row = self.cursor.fetchone()
        if row:
            return {"LL": row[0], "L": row[1], "H": row[2], "HH": row[3]}
        return None
    
    def upsert_manual_thresholds(self, class_id: int, prop_id: int, 
                                  ll: Optional[float], l: Optional[float],
                                  h: Optional[float], hh: Optional[float]):
        """Insert ou update des seuils manuels"""
        self.cursor.execute("""
            INSERT INTO seprop_manual_thresholds (class_id, prop_id, ll, l, h, hh)
            VALUES (?, ?, ?, ?, ?, ?)
            ON CONFLICT(class_id, prop_id) DO UPDATE SET
                ll = excluded.ll, l = excluded.l, h = excluded.h, hh = excluded.hh
        """, (class_id, prop_id, ll, l, h, hh))
        self.conn.commit()
    
    # ========== UTILISATEURS ==========
    
    def get_user_by_username(self, username: str) -> Optional[Tuple[int, str, str]]:
        """Récupère (id, username, role)"""
        self.cursor.execute(
            "SELECT id, username, role FROM se_users WHERE LOWER(username) = LOWER(?)",
            (username,)
        )
        return self.cursor.fetchone()
    
    def insert_user(self, username: str, role: str = 'user') -> Optional[int]:
        """Insère un nouvel utilisateur (retourne None si existe déjà)"""
        try:
            self.cursor.execute(
                "INSERT INTO se_users (username, role) VALUES (?, ?)",
                (username, role)
            )
            self.conn.commit()
            return self.cursor.lastrowid
        except sqlite3.IntegrityError:
            return None
    
    # ========== SOUMISSIONS ==========
    
    def get_pending_submissions(self) -> List[Tuple[int, int, str, str, str]]:
        """Retourne (id, user_id, description, status, created_at)"""
        self.cursor.execute("""
            SELECT id, user_id, description, status, created_at 
            FROM se_submissions 
            WHERE status = 'pending'
            ORDER BY created_at
        """)
        return self.cursor.fetchall()
    
    def get_submission_changes(self, submission_id: int) -> Optional[str]:
        """Récupère le JSON des changements"""
        self.cursor.execute(
            "SELECT changes_json FROM se_submissions WHERE id = ?",
            (submission_id,)
        )
        row = self.cursor.fetchone()
        return row[0] if row else None
    
    def insert_submission(self, user_id: int, description: str, changes_json: str) -> int:
        """Insère une nouvelle soumission"""
        self.cursor.execute("""
            INSERT INTO se_submissions (user_id, description, changes_json)
            VALUES (?, ?, ?)
        """, (user_id, description, changes_json))
        self.conn.commit()
        return self.cursor.lastrowid
    
    def update_submission_status(self, submission_id: int, status: str, validator_id: int):
        """Met à jour le statut d'une soumission"""
        self.cursor.execute("""
            UPDATE se_submissions 
            SET status = ?, validated_by = ?, validated_at = CURRENT_TIMESTAMP
            WHERE id = ?
        """, (status, validator_id, submission_id))
        self.conn.commit()
    
    # ========== EVENTS ==========
    def store_event(self, event):
        payload_json = json.dumps(event.payload) if event.payload else None
        self.cursor.execute("""
            INSERT INTO se_events (event_type, source, entity, payload, severity)
            VALUES (?, ?, ?, ?, ?)
        """, (event.event_type, event.source, event.entity, payload_json, event.severity))
        self.commit()

    def get_events(self, entity=None, limit=50):
        query = "SELECT * FROM se_events"
        params = ()
        if entity:
            query += " WHERE entity = ?"
            params = (entity,)
        query += " ORDER BY timestamp DESC LIMIT ?"
        params += (limit,)
        return self.cursor.execute(query, params).fetchall()  # Return list tuples, map to Event if needed


    # ========== UTILITAIRES ==========
    
    def commit(self):
        """Commit explicite si besoin"""
        self.conn.commit()
    
    def close(self):
        """Ferme la connexion"""
        self.conn.commit()
        self.conn.close()