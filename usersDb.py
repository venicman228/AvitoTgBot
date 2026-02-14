import sqlite3

class sql_requests:

    #CONNECT TO DB
    connect = sqlite3.connect("users.db")
    cursor = connect.cursor()

    ### ADD USER DB
    @classmethod
    def add_user_in_db(cls, user_id):
        cls.cursor.execute(f"SELECT id FROM login_id WHERE id = {user_id}")
        data = cls.cursor.fetchone()
        if data is None:
            cls.cursor.execute("INSERT INTO login_id (id, search_link, is_search_active) VALUES(?, ?, ?);", (user_id, "avito.ru", 0))
            cls.connect.commit()

    ### TAKE ALL USERS_ID FROM DB
    @classmethod
    def all_users_id(cls):
        cls.cursor.execute("SELECT DISTINCT id FROM login_id")
        return cls.cursor.fetchall()

    ### GETTING ACTIVE_SEARCH_LINK FROM DB
    @classmethod
    def get_active_link(cls, link_number, user_id):
        if link_number == "1":
            cls.cursor.execute(f"SELECT search_link FROM login_id WHERE id = ?;", (user_id,))
            return cls.cursor.fetchall()[0][0]
        elif link_number == "2":
            cls.cursor.execute(f"SELECT search_link_2 FROM login_id WHERE id = ?;", (user_id,))
            return cls.cursor.fetchall()[0][0]
        elif link_number == "3":
            cls.cursor.execute(f"SELECT search_link_3 FROM login_id WHERE id = ?;", (user_id,))
            return cls.cursor.fetchall()[0][0]

    ### REPLACE ACTIVE_SEARCH_LINK IN DB
    @classmethod
    def replace_active_link(cls, link_number, new_link, user_id):
        if link_number == "1":
            cls.cursor.execute(f"UPDATE login_id SET search_link = ? WHERE id = ?;", (new_link, user_id))
            cls.connect.commit()
        elif link_number == "2":
            cls.cursor.execute(f"UPDATE login_id SET search_link_2 = ? WHERE id = ?;", (new_link, user_id))
            cls.connect.commit()
        elif link_number == "3":
            cls.cursor.execute(f"UPDATE login_id SET search_link_3 = ? WHERE id = ?;", (new_link, user_id))
            cls.connect.commit()

    ### CHANGE IS_SEARCH_ACTIVE FLAG
    @classmethod
    def change_is_search_active(cls, user_id, search_flag):
        cls.cursor.execute(f"UPDATE login_id SET is_search_active = ? WHERE id = ?", (search_flag, user_id))
        cls.connect.commit()

    ### RETURN IS_SEARCH_ACTIVE FLAG
    @classmethod
    def get_is_search_active(cls, user_id):
        cls.cursor.execute(f"SELECT is_search_active FROM login_id WHERE id = ?;", (user_id,))
        return cls.cursor.fetchall()[0][0]

