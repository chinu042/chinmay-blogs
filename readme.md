database schema = {
    1. users = {
        user_id (p_key),user_name,user_email,user_password
    }
    2. blogs = {
        blog_id (p_key) auto_inc,blog_title,blog_content,blog_date,user_id (f_key)
    }
    3. comments = {
        comment_id (p_key), comment_content,blog_id (f_key),comment_date,user_id (f_key)
    }
}