# core/database.py
import statistics  # Pour median et stdev
import sqlite3
from rich.console import Console
from rich.prompt import Prompt, Confirm
from rich.panel import Panel
from core.models.event import Event
from core.inference import ForwardEngine, BackwardEngine
from core.services.EntityService import EntityService
import json
import uuid
import datetime  # Ensure at top

console = Console()
DB_FILE = "data/XXpert.db"
DEBUG = True  # Ou False pour désactiver

class KnowledgeBase:
    def __init__(self):
        self.conn = sqlite3.connect(DB_FILE)
        self.cursor = self.conn.cursor()
        self._setup_db()

        self.forward_engine = ForwardEngine(self)
        self.backward_engine = BackwardEngine(self)
        self._register_default_rules()        

        self.entity_service = EntityService()


    def _setup_db(self):
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
                PRIMARY KEY (inst_id, prop_id)
            );

            -- Nouvelle table pour les statistiques par (classe, propriété numérique)
            CREATE TABLE IF NOT EXISTS seprop_stats (
                class_id INTEGER,
                prop_id INTEGER,
                instance_count INTEGER DEFAULT 0,   -- nb d'instances avec valeur non nulle
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

            -- Optionnel : table pour seuils manuels (expert)
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
                payload TEXT, 
                severity TEXT DEFAULT 'info',
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
            );

        """)
        self.conn.commit()

        if not self.get_class_id("Animal"):
            self.cursor.execute("INSERT INTO seclass (name) VALUES ('Animal')")
            self.conn.commit()

        # Admin par défaut
        self.cursor.execute("SELECT COUNT(*) FROM se_users WHERE username = 'admin'")
        if self.cursor.fetchone()[0] == 0:
            self.cursor.execute("INSERT INTO se_users (username, role) VALUES ('admin', 'admin')")
            self.commit()


    def commit(self):
        self.conn.commit()

    def close(self):
        self.commit()
        self.conn.close()

    # --- Utilitaires ---
    def get_class_id(self, name):
        self.cursor.execute("SELECT id FROM seclass WHERE LOWER(name) = LOWER(?)", (name,))
        row = self.cursor.fetchone()
        return row[0] if row else None

    def get_property_id(self, name):
        self.cursor.execute("SELECT id FROM seprop WHERE LOWER(name) = LOWER(?)", (name,))
        row = self.cursor.fetchone()
        return row[0] if row else None

    def get_all_class_names(self):
        self.cursor.execute("SELECT name FROM seclass ORDER BY name")
        return [r[0] for r in self.cursor.fetchall()]

    def get_all_property_names(self):
        self.cursor.execute("SELECT name FROM seprop ORDER BY name")
        return [r[0] for r in self.cursor.fetchall()]

    # Ajout DEV 25-12-27
    # def get_all_classesOLD(self):
    #     self.cursor.execute("SELECT id, name, parent_id FROM seclass ORDER BY name")
    #     rows = self.cursor.fetchall()
    #     if DEBUG:  # Assume DEBUG global ou passe via self.debug = True
    #         print(f"get_all_classes: fetched {len(rows)} rows: {rows}")
    #     return rows        

    def get_all_classes(self):
        self.cursor.execute("""
            SELECT c.id, c.name, p.name AS parent_name 
            FROM seclass c LEFT JOIN seclass p ON c.parent_id = p.id 
            ORDER BY c.name
        """)

        rows = self.cursor.fetchall()
        if DEBUG:  # Assume DEBUG global ou passe via self.debug = True
            print(f"get_all_classes: fetched {len(rows)} rows: {rows}")
        return rows        

    #--------------------------------------------------------------------------
    # 2025-12-30 
    #   database.py
    #  - Ajout de delete_property (avec vérifications)
    #  - Ajout de modify_property (ex: changer type)
    #       Mise à jour de modify_property pour supporter rename et change type

    def delete_property(self, prop_name):
        if not prop_name or not isinstance(prop_name, str):
            return False

        prop_name = prop_name.strip().lower()
        if not prop_name:
            return False

        p_id = self.get_property_id(prop_name)
        if not p_id:
            return False  # Propriété inconnue

        try:
            # Supprimer les liens avec classes
            self.cursor.execute("DELETE FROM seclass_prop WHERE prop_id = ?", (p_id,))
            # Supprimer les valeurs d'instances
            self.cursor.execute("DELETE FROM seinst_value WHERE prop_id = ?", (p_id,))
            # Supprimer les stats et thresholds
            self.cursor.execute("DELETE FROM seprop_stats WHERE prop_id = ?", (p_id,))
            self.cursor.execute("DELETE FROM seprop_manual_thresholds WHERE prop_id = ?", (p_id,))
            # Supprimer la propriété elle-même
            self.cursor.execute("DELETE FROM seprop WHERE id = ?", (p_id,))
            self.commit()
            return True
        except sqlite3.Error:
            return False

    # database.py - Mise à jour de modify_property pour supporter rename et change type
    def modify_property(self, prop_name, new_name=None, new_type=None):
        if not prop_name or not isinstance(prop_name, str):
            return False

        prop_name = prop_name.strip().lower()
        if not prop_name:
            return False

        p_id = self.get_property_id(prop_name)
        if not p_id:
            return False  # Propriété inconnue

        updated = False

        if new_name:
            if not isinstance(new_name, str) or not new_name.strip():
                return False
            new_name = new_name.strip().lower()

            if self.get_property_id(new_name):
                return False  # Nouveau nom déjà pris

            try:
                self.cursor.execute("UPDATE seprop SET name = ? WHERE id = ?", (new_name, p_id))
                updated = True
            except sqlite3.Error:
                return False

        if new_type:
            valid_types = {"string", "bool", "int", "float"}
            if new_type not in valid_types:
                return False

            try:
                self.cursor.execute("UPDATE seprop SET type = ? WHERE id = ?", (new_type, p_id))
                updated = True
                # Note: Changer type peut nécessiter cleanup des valeurs existantes si incompatible, mais omis pour simplicité
            except sqlite3.Error:
                return False

        if updated:
            self.commit()
            return True

        return False  # Rien à modifier

    # Ajout DEV 25-12-27
    def get_all_properties(self):
        self.cursor.execute("SELECT id, name, type FROM seprop ORDER BY name")
        return self.cursor.fetchall()
    # Ajout DEV 25-12-27
    def get_all_instances_global(self):
        self.cursor.execute("""
            SELECT i.id, i.name, c.name AS class_name 
            FROM seinst i JOIN seclass c ON i.class_id = c.id 
            ORDER BY c.name, i.name
        """)
        return self.cursor.fetchall()

    def get_all_events(self, limit=100):
        # Alias pour get_events sans entity
        return self.get_events(entity=None, limit=limit)


    # --- Classes ---
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
        self.store_event(event)
        return True, event  # return True, Event("class_added", "database", entity=name)  # Return tuple (success, event)


    # --- Propriétés ---
    # database.py - Add 'uuid' to valid_types in add_property
    import uuid  # Add at top if not present

    def add_property(self, name, ptype="string"):
        if not name or not isinstance(name, str):
            return False
        name = name.strip().lower()
        if not name:
            return False
        valid_types = {"string", "bool", "int", "float", "date", "datetime", "time", "json", "timedelta", "uuid"}  # Added 'uuid'
        if ptype not in valid_types:
            return False
        if self.get_property_id(name):
            return False
        try:
            self.cursor.execute("INSERT INTO seprop (name, type) VALUES (?, ?)", (name, ptype))
            self.commit()
            return True
        except sqlite3.IntegrityError:
            return False

    def link_property_to_class(self, class_name, prop_name):
        c_id = self.get_class_id(class_name)
        p_id = self.get_property_id(prop_name)
        if not c_id or not p_id:
            console.print("[red]Classe ou propriété inconnue[/]")
            return False
        try:
            self.cursor.execute("INSERT INTO seclass_prop (class_id, prop_id) VALUES (?, ?)", (c_id, p_id))
            self.commit()
            console.print(Panel(f"Propriété [cyan]'{prop_name}'[/] liée à [green]'{class_name}'[/]", style="cyan"))
            return True
        except sqlite3.IntegrityError:
            console.print("[yellow]Déjà liée[/]")
            return False

    # database.py - attach_property_to_class with validation rules
    def attach_property_to_class(self, class_name, prop_name):
        if not class_name or not isinstance(class_name, str):
            return False
        if not prop_name or not isinstance(prop_name, str):
            return False
        class_name = class_name.strip()
        prop_name = prop_name.strip().lower()
        if not class_name or not prop_name:
            return False
        c_id = self.get_class_id(class_name)
        if not c_id:
            return False
        p_id = self.get_property_id(prop_name)
        if not p_id:
            return False
        try:
            self.cursor.execute("INSERT OR IGNORE INTO seclass_prop (class_id, prop_id) VALUES (?, ?)", (c_id, p_id))
            self.commit()
            return True
        except sqlite3.Error:
            return False

    # --- Instances ---
    # database.py - add_instance with validation rules
    def add_instance(self, name, class_name):
        if not name or not isinstance(name, str):
            return False
        if not class_name or not isinstance(class_name, str):
            return False
        name = name.strip()
        class_name = class_name.strip()
        if not name or not class_name:
            return False
        c_id = self.get_class_id(class_name)
        if not c_id:
            return False
        self.cursor.execute("SELECT 1 FROM seinst WHERE LOWER(name)=LOWER(?) AND class_id=?", (name, c_id))
        if self.cursor.fetchone():
            return False
        try:
            self.cursor.execute("INSERT INTO seinst (name, class_id) VALUES (?, ?)", (name, c_id))
            self.commit()
            return True
        except sqlite3.IntegrityError:
            return False

    def get_all_instances(self, class_name):
        c_id = self.get_class_id(class_name)
        if not c_id:
            return []
        self.cursor.execute("SELECT name FROM seinst WHERE class_id=? ORDER BY name", (c_id,))
        return [r[0] for r in self.cursor.fetchall()]

    # --- Valeurs ---

    def get_instance_value(self, inst_name, class_name, prop_name):
        if not inst_name or not isinstance(inst_name, str):
            return None
        if not class_name or not isinstance(class_name, str):
            return None
        if not prop_name or not isinstance(prop_name, str):
            return None

        inst_name = inst_name.strip()
        class_name = class_name.strip()
        prop_name = prop_name.strip().lower()

        if not inst_name or not class_name or not prop_name:
            return None

        class_id = self.get_class_id(class_name)
        if not class_id:
            return None

        self.cursor.execute("SELECT id FROM seinst WHERE LOWER(name) = LOWER(?) AND class_id = ?", (inst_name, class_id))
        row = self.cursor.fetchone()
        if not row:
            return None
        inst_id = row[0]

        prop_id = self.get_property_id(prop_name)
        if not prop_id:
            return None

        self.cursor.execute("SELECT value FROM seinst_value WHERE inst_id = ? AND prop_id = ?", (inst_id, prop_id))
        row = self.cursor.fetchone()
        if not row:
            return None

        stored = row[0]
        if stored is None:
            return None

        ptype = self.get_property_type(prop_name)
        try:
            if ptype == "bool":
                return stored.lower() in ("true", "1", "yes")
            elif ptype == "int":
                return int(stored)
            elif ptype == "float":
                return float(stored)
            elif ptype == "date":
                return datetime.date.fromisoformat(stored)
            elif ptype == "datetime":
                return datetime.datetime.fromisoformat(stored)
            elif ptype == "time":
                return datetime.time.fromisoformat(stored)
            elif ptype == "json":
                return json.loads(stored)
            elif ptype == "timedelta":
                return datetime.timedelta(seconds=float(stored))
            elif ptype == "uuid":
                return uuid.UUID(stored)
            else:  # string or default
                return stored
        except ValueError:
            return None  # Invalid stored value for type


    # database.py - instance_exists with validation rules
    def instance_exists(self, name, class_name):
        if not name or not isinstance(name, str):
            return False
        if not class_name or not isinstance(class_name, str):
            return False
        name = name.strip()
        class_name = class_name.strip()
        if not name or not class_name:
            return False
        c_id = self.get_class_id(class_name)
        if not c_id:
            return False
        self.cursor.execute("SELECT 1 FROM seinst WHERE LOWER(name)=LOWER(?) AND class_id=?", (name, c_id))
        return bool(self.cursor.fetchone())

    # --- set_instance_value ---
    def set_instance_value(self, inst_name, class_name, prop_name, value):
        if not inst_name or not isinstance(inst_name, str):
            return False
        if not class_name or not isinstance(class_name, str):
            return False
        if not prop_name or not isinstance(prop_name, str):
            return False

        inst_name = inst_name.strip()
        class_name = class_name.strip()
        prop_name = prop_name.strip().lower()

        if not inst_name or not class_name or not prop_name:
            return False

        class_id = self.get_class_id(class_name)
        if not class_id:
            return False

        self.cursor.execute("SELECT id FROM seinst WHERE LOWER(name) = LOWER(?) AND class_id = ?", (inst_name, class_id))
        row = self.cursor.fetchone()
        if not row:
            return False
        inst_id = row[0]

        prop_id = self.get_property_id(prop_name)
        if not prop_id:
            return False

        ptype = self.get_property_type(prop_name)
        if value is not None:
            try:
                if ptype == "bool":
                    if not isinstance(value, bool):
                        return False
                elif ptype == "int":
                    value = int(value)
                elif ptype == "float":
                    value = float(value)
                elif ptype == "string":
                    if not isinstance(value, str):
                        return False
                elif ptype == "date":
                    if isinstance(value, str):
                        value = datetime.date.fromisoformat(value)
                    elif isinstance(value, datetime.date):
                        pass
                    else:
                        return False
                    stored = value.isoformat()
                elif ptype == "datetime":
                    if isinstance(value, str):
                        value = datetime.datetime.fromisoformat(value)
                    elif isinstance(value, datetime.datetime):
                        pass
                    else:
                        return False
                    stored = value.isoformat()
                elif ptype == "time":
                    if isinstance(value, str):
                        value = datetime.time.fromisoformat(value)
                    elif isinstance(value, datetime.time):
                        pass
                    else:
                        return False
                    stored = value.isoformat()
                elif ptype == "json":
                    stored = json.dumps(value)
                elif ptype == "timedelta":
                    if isinstance(value, str):
                        value = datetime.timedelta(seconds=float(value))
                    elif isinstance(value, datetime.timedelta):
                        pass
                    else:
                        return False
                    stored = str(value.total_seconds())
                elif ptype == "uuid":
                    if isinstance(value, str):
                        value = uuid.UUID(value)
                    elif isinstance(value, uuid.UUID):
                        pass
                    else:
                        return False
                    stored = str(value)
                else:
                    return False  # Type inconnu
            except (ValueError, TypeError):
                return False  # Conversion/serialize échouée

        stored = None if value is None else ("true" if value is True else "false" if value is False else str(value))

        try:
            self.cursor.execute("""
                INSERT INTO seinst_value (inst_id, prop_id, value)
                VALUES (?, ?, ?)
                ON CONFLICT(inst_id, prop_id) DO UPDATE SET value = excluded.value
            """, (inst_id, prop_id, stored))
            self.commit()

            if isinstance(value, (int, float)):
                if ptype in ("int", "float"):
                    self._update_stats(class_id, prop_id, value)

            return True
        except sqlite3.Error:
            return False

    def get_property_type(self, prop_name):
        if not prop_name or not isinstance(prop_name, str):
            return None
        
        prop_name = prop_name.strip().lower()
        if not prop_name:
            return None

        self.cursor.execute("SELECT type FROM seprop WHERE LOWER(name) = ?", (prop_name,))
        row = self.cursor.fetchone()
        return row[0] if row else None

    def get_all_props_for_classOLD(self, class_name):
        c_id = self.get_class_id(class_name)
        if not c_id:
            return []
        props = set()
        current = c_id
        while current:
            self.cursor.execute("SELECT p.name FROM seprop p JOIN seclass_prop cp ON p.id=cp.prop_id WHERE cp.class_id=?", (current,))
            for r in self.cursor.fetchall():
                props.add(r[0])
            self.cursor.execute("SELECT parent_id FROM seclass WHERE id=?", (current,))
            row = self.cursor.fetchone()
            current = row[0] if row else None
        return sorted(props)


    def get_all_props_for_class(self, class_name):
        c_id = self.get_class_id(class_name)
        if not c_id:
            return []
        self.cursor.execute("""
            SELECT p.name FROM seprop p
            JOIN seclass_prop cp ON p.id = cp.prop_id
            WHERE cp.class_id = ?
            ORDER BY p.name
        """, (c_id,))
        return [r[0] for r in self.cursor.fetchall()]



    # --- Pour l'arbre des classes ---
    def get_hierarchyOLD(self):
        self.cursor.execute("""
            WITH RECURSIVE tree(id, name, parent_id, level) AS (
                SELECT id, name, parent_id, 0 FROM seclass WHERE parent_id IS NULL
                UNION ALL
                SELECT c.id, c.name, c.parent_id, t.level+1 FROM seclass c JOIN tree t ON c.parent_id = t.id
            )
            SELECT id, name, parent_id, level FROM tree ORDER BY level, name
        """)
        return self.cursor.fetchall()

    def get_hierarchy(self):
        self.cursor.execute("""
            WITH RECURSIVE hierarchy(id, name, parent_id, level) AS (
                SELECT id, name, parent_id, 0 FROM seclass WHERE parent_id IS NULL
                UNION ALL
                SELECT c.id, c.name, c.parent_id, h.level + 1
                FROM seclass c JOIN hierarchy h ON c.parent_id = h.id
            )
            SELECT id, name, parent_id, level FROM hierarchy ORDER BY level, name
        """)
        rows = self.cursor.fetchall()
        if DEBUG:
            print(f"get_hierarchy: fetched {len(rows)} rows: {rows}")
        return rows


    def _update_statsOLD(self, class_id, prop_id, value):
        if value is None or not isinstance(value, (int, float)):
            return

        # Récupérer stats actuelles
        self.cursor.execute("""
            SELECT instance_count, min_value, max_value, mean_value 
            FROM seprop_stats WHERE class_id=? AND prop_id=?
        """, (class_id, prop_id))
        row = self.cursor.fetchone()

        if row:
            count, min_v, max_v, mean = row
            count += 1
            new_mean = mean + (value - mean) / count
            # Mise à jour incrémentale simple (pour variance plus tard si besoin)
            self.cursor.execute("""
                UPDATE seprop_stats SET 
                    instance_count=?, min_value=?, max_value=?, mean_value=?, updated_at=CURRENT_TIMESTAMP
                WHERE class_id=? AND prop_id=?
            """, (count, min(min_v, value), max(max_v, value), new_mean, class_id, prop_id))
        else:
            self.cursor.execute("""
                INSERT INTO seprop_stats (class_id, prop_id, instance_count, min_value, max_value, mean_value)
                VALUES (?, ?, 1, ?, ?, ?)
            """, (class_id, prop_id, value, value, value))
        self.conn.commit()

        # Recalculer médiane et écart-type (plus lourd mais précis)
        self._recalculate_full_stats(class_id, prop_id)



# database.py - _update_stats améliorée
    def _update_stats(self, class_id, prop_id, value):
        if value is None or not isinstance(value, (int, float)):
            return False

        try:
            # Récupérer stats actuelles
            self.cursor.execute("""
                SELECT instance_count, min_value, max_value, mean_value 
                FROM seprop_stats WHERE class_id=? AND prop_id=?
            """, (class_id, prop_id))
            row = self.cursor.fetchone()

            if row:
                count, min_v, max_v, mean = row
                if count is None:  # Sécurité si données corrompues
                    count = 0
                count += 1
                # Formule incrémentale stable pour la moyenne
                new_mean = mean + (value - mean) / count if mean is not None else value
                new_min = min(min_v, value) if min_v is not None else value
                new_max = max(max_v, value) if max_v is not None else value

                self.cursor.execute("""
                    UPDATE seprop_stats SET 
                        instance_count=?, min_value=?, max_value=?, mean_value=?, updated_at=CURRENT_TIMESTAMP
                    WHERE class_id=? AND prop_id=?
                """, (count, new_min, new_max, new_mean, class_id, prop_id))
            else:
                self.cursor.execute("""
                    INSERT INTO seprop_stats 
                    (class_id, prop_id, instance_count, min_value, max_value, mean_value)
                    VALUES (?, ?, 1, ?, ?, ?)
                """, (class_id, prop_id, value, value, value))

            self.conn.commit()
            self._recalculate_full_stats(class_id, prop_id)
            return True
        except sqlite3.Error:
            return False






    def _register_default_rules(self):
        # Règles circuit électrique
        self.forward_engine.add_rule(['tension', 'intensite'], 'puissance', lambda u, i: u * i, "W")
        self.forward_engine.add_rule(['tension', 'intensite'], 'resistance', lambda u, i: u / i if i != 0 else None, "Ω")
        self.forward_engine.add_rule(['resistance', 'intensite'], 'tension', lambda r, i: r * i, "V")
        self.forward_engine.add_rule(['puissance', 'tension'], 'intensite', lambda p, u: p / u if u != 0 else None, "A")
        self.forward_engine.add_rule(['resistance', 'intensite'], 'puissance', lambda r, i: r * i**2, "W")

        # Même règles pour backward (inversées)
        self.backward_engine.add_rule('puissance', ['tension', 'intensite'], lambda u, i: u * i, "W")
        self.backward_engine.add_rule('resistance', ['tension', 'intensite'], lambda u, i: u / i if i != 0 else None, "Ω")
        self.backward_engine.add_rule('tension', ['resistance', 'intensite'], lambda r, i: r * i, "V")
        self.backward_engine.add_rule('intensite', ['puissance', 'tension'], lambda p, u: p / u if u != 0 else None, "A")
        # Ajoute ici tes règles débit/dP quand prêt (ex. log)

    # database.py - _recalculate_full_stats optimisée
    def _recalculate_full_stats(self, class_id, prop_id):
        try:
            self.cursor.execute("""
                SELECT v.value FROM seinst_value v
                JOIN seinst i ON v.inst_id = i.id
                WHERE i.class_id = ? AND v.prop_id = ? AND v.value IS NOT NULL
            """, (class_id, prop_id))
            
            values = []
            for row in self.cursor.fetchall():
                try:
                    values.append(float(row[0]))
                except (ValueError, TypeError):
                    continue  # Ignorer les valeurs non convertibles

            if not values:
                # Plus aucune valeur numérique → supprimer les stats
                self.cursor.execute("DELETE FROM seprop_stats WHERE class_id=? AND prop_id=?", (class_id, prop_id))
                self.conn.commit()
                return

            median = statistics.median(values)
            stdev = statistics.stdev(values) if len(values) > 1 else 0.0

            self.cursor.execute("""
                UPDATE seprop_stats SET 
                    median_value=?, std_dev=?, updated_at=CURRENT_TIMESTAMP
                WHERE class_id=? AND prop_id=?
            """, (median, stdev, class_id, prop_id))
            self.conn.commit()
        except sqlite3.Error:
            pass  # Silencieux : si erreur, on laisse les anciennes stats


    def _recalculate_full_statsOLD(self, class_id, prop_id):
        self.cursor.execute("""
            SELECT v.value FROM seinst_value v
            JOIN seinst i ON v.inst_id = i.id
            WHERE i.class_id = ? AND v.prop_id = ? AND v.value IS NOT NULL
        """, (class_id, prop_id))
        values = []
        for row in self.cursor.fetchall():
            try:
                values.append(float(row[0]))
            except:
                pass

        if not values:
            self.cursor.execute("DELETE FROM seprop_stats WHERE class_id=? AND prop_id=?", (class_id, prop_id))
            self.conn.commit()
            return

        median = statistics.median(values)
        stdev = statistics.stdev(values) if len(values) > 1 else 0

        self.cursor.execute("""
            UPDATE seprop_stats SET 
                median_value=?, std_dev=?, updated_at=CURRENT_TIMESTAMP
            WHERE class_id=? AND prop_id=?
        """, (median, stdev, class_id, prop_id))
        self.conn.commit()



    def get_thresholds(self, class_name, prop_name):
        c_id = self.get_class_id(class_name)
        p_id = self.get_property_id(prop_name)
        if not c_id or not p_id:
            return None

        thresholds = {"LL": None, "L": None, "M": None, "H": None, "HH": None}

        # 1. Seuils manuels (priorité)
        self.cursor.execute("""
            SELECT ll, l, h, hh FROM seprop_manual_thresholds
            WHERE class_id=? AND prop_id=?
        """, (c_id, p_id))
        row = self.cursor.fetchone()
        if row:
            thresholds["LL"], thresholds["L"], thresholds["H"], thresholds["HH"] = row

        # 2. Stats auto-apprises
        self.cursor.execute("""
            SELECT mean_value, median_value, std_dev FROM seprop_stats
            WHERE class_id=? AND prop_id=?
        """, (c_id, p_id))
        row = self.cursor.fetchone()
        if row:
            mean, median, stdev = row
            thresholds["M"] = median or mean

            if stdev > 0:
                if thresholds["L"] is None:
                    thresholds["L"] = mean - stdev
                if thresholds["H"] is None:
                    thresholds["H"] = mean + stdev
                if thresholds["LL"] is None:
                    thresholds["LL"] = mean - 2 * stdev
                if thresholds["HH"] is None:
                    thresholds["HH"] = mean + 2 * stdev

        return thresholds

    def set_manual_thresholds(self, class_name, prop_name, ll=None, l=None, h=None, hh=None):
        c_id = self.get_class_id(class_name)
        p_id = self.get_property_id(prop_name)
        if not c_id or not p_id:
            return False
        self.cursor.execute("""
            INSERT INTO seprop_manual_thresholds (class_id, prop_id, ll, l, h, hh)
            VALUES (?, ?, ?, ?, ?, ?)
            ON CONFLICT(class_id, prop_id) DO UPDATE SET
                ll=excluded.ll, l=excluded.l, h=excluded.h, hh=excluded.hh
        """, (c_id, p_id, ll, l, h, hh))
        self.conn.commit()
        return True

    def ask_and_set_properties(self, inst_name, class_name):
        props = self.get_all_props_for_class(class_name)
        if not props:
            console.print("[yellow]Aucune propriété disponible[/]")
            return

        console.print(Panel(f"[bold]Saisie des propriétés pour [green]{inst_name}[/] ({class_name})[/bold]"))

        for prop in props:
            current = self.get_instance_value(inst_name, class_name, prop)
            if current is not None:
                console.print(f"  [dim]{prop} : {current} (déjà défini)[/]")
                if not Confirm.ask("Modifier ?", default=False):
                    continue

            ptype = self.get_property_type(prop)

            if ptype == "bool":
                prompt_text = f"[cyan]{prop}[/] ? (oui/true / non/false / X inconnu)"
                default = "oui"
            elif ptype in ("int", "float"):
                prompt_text = f"[cyan]{prop}[/] ? (nombre ou X inconnu)"
                default = ""
            else:
                prompt_text = f"[cyan]{prop}[/] ? (texte ou X inconnu)"
                default = ""

            val_str = Prompt.ask(prompt_text, default=default)

            if val_str.upper() == "X":
                val = None
            else:
                try:
                    if ptype == "bool":
                        val = val_str.lower() in ("true", "vrai", "oui", "o", "yes", "y", "1")
                    elif ptype == "int":
                        val = int(val_str)
                    elif ptype == "float":
                        val = float(val_str)
                    else:
                        val = val_str
                except ValueError:
                    console.print(f"[red]Valeur invalide pour {ptype}, ignorée[/]")
                    val = None

            self.set_instance_value(inst_name, class_name, prop, val)

    def get_user_id(self, username):
        self.cursor.execute("SELECT id FROM se_users WHERE LOWER(username)=LOWER(?)", (username,))
        row = self.cursor.fetchone()
        return row[0] if row else None

    def get_user_role(self, username):
        self.cursor.execute("SELECT role FROM se_users WHERE LOWER(username) = LOWER(?)", (username,))
        row = self.cursor.fetchone()
        return row[0] if row else None

    def create_user(self, username, role='user'):
        try:
            self.cursor.execute("INSERT INTO se_users (username, role) VALUES (?, ?)", (username, role))
            self.commit()
            return True
        except sqlite3.IntegrityError:
            return False

    def get_pending_submissions(self):
        self.cursor.execute("SELECT id, user_id, description, status, created_at FROM se_submissions WHERE status = 'pending'")
        return self.cursor.fetchall()

    def merge_submission(self, submission_id, validator_id):
        self.cursor.execute("SELECT changes_json FROM se_submissions WHERE id = ?", (submission_id,))
        row = self.cursor.fetchone()
        if not row:
            return False

        changes = json.loads(row[0])
        success = True
        for change in changes:
            action = change['action']
            data = change['data']
            if action == 'add_class':
                success &= self.add_class(data['name'], data.get('parent'))
            elif action == 'add_instance':
                success &= self.add_instance(data['name'], data['class_name'])
            # Ajoute pour autres actions (add_prop, etc.)

        if success:
            self.cursor.execute("UPDATE se_submissions SET status = 'validated', validated_by = ?, validated_at = CURRENT_TIMESTAMP WHERE id = ?", (validator_id, submission_id))
            self.commit()
        return success

    def reject_submission(self, submission_id, validator_id):
        self.cursor.execute("UPDATE se_submissions SET status = 'rejected', validated_by = ?, validated_at = CURRENT_TIMESTAMP WHERE id = ?", (validator_id, submission_id))
        self.commit()
        return True

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

    # core/database.py (repo, no UI/logic; pure data access)
    # ... (existing, remove any print/Prompt; return data or success)
    def class_exists(self, name):
        return bool(self.get_class_id(name))
    # No store_event here; services handle

           