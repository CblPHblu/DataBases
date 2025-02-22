PGDMP  &    	                |            tutoring_service    17.2 (Debian 17.2-1.pgdg120+1)    17.2 (Debian 17.2-1.pgdg120+1) 7    r           0    0    ENCODING    ENCODING        SET client_encoding = 'UTF8';
                           false            s           0    0 
   STDSTRINGS 
   STDSTRINGS     (   SET standard_conforming_strings = 'on';
                           false            t           0    0 
   SEARCHPATH 
   SEARCHPATH     8   SELECT pg_catalog.set_config('search_path', '', false);
                           false            u           1262    16384    tutoring_service    DATABASE     {   CREATE DATABASE tutoring_service WITH TEMPLATE = template0 ENCODING = 'UTF8' LOCALE_PROVIDER = libc LOCALE = 'en_US.utf8';
     DROP DATABASE tutoring_service;
                     postgres    false            �            1255    16505 w   add_tutor_with_schedule(integer, integer, text, double precision, text, time without time zone, time without time zone) 	   PROCEDURE     %  CREATE PROCEDURE public.add_tutor_with_schedule(IN p_user_id integer, IN p_subject_id integer, IN p_description text, IN p_hourly_rate double precision, IN p_day_of_week text, IN p_start_time time without time zone, IN p_end_time time without time zone)
    LANGUAGE plpgsql
    AS $$
            BEGIN
                INSERT INTO Tutors (user_id, subject_id, description, hourly_rate)
                VALUES (p_user_id, p_subject_id, p_description, p_hourly_rate);

                INSERT INTO Schedules (tutor_id, day_of_week, start_time, end_time)
                VALUES (
                    (SELECT tutor_id FROM Tutors WHERE user_id = p_user_id),
                    p_day_of_week,
                    p_start_time,
                    p_end_time
                );
            END;
            $$;
 �   DROP PROCEDURE public.add_tutor_with_schedule(IN p_user_id integer, IN p_subject_id integer, IN p_description text, IN p_hourly_rate double precision, IN p_day_of_week text, IN p_start_time time without time zone, IN p_end_time time without time zone);
       public               postgres    false            �            1255    16504 !   get_average_tutor_rating(integer)    FUNCTION     �  CREATE FUNCTION public.get_average_tutor_rating(tutor_id integer) RETURNS double precision
    LANGUAGE plpgsql
    AS $$
            DECLARE
                avg_rating FLOAT;
            BEGIN
                SELECT AVG(rating) INTO avg_rating
                FROM Reviews
                WHERE tutor_id = tutor_id;
                RETURN avg_rating;
            END;
            $$;
 A   DROP FUNCTION public.get_average_tutor_rating(tutor_id integer);
       public               postgres    false            �            1255    16502 "   update_tutor_rating_after_review()    FUNCTION     �  CREATE FUNCTION public.update_tutor_rating_after_review() RETURNS trigger
    LANGUAGE plpgsql
    AS $$
            BEGIN
                UPDATE Tutors
                SET rating = (
                    SELECT AVG(rating)
                    FROM Reviews
                    WHERE tutor_id = NEW.tutor_id
                )
                WHERE tutor_id = NEW.tutor_id;
                RETURN NEW;
            END;
            $$;
 9   DROP FUNCTION public.update_tutor_rating_after_review();
       public               postgres    false            �            1259    16439    requests    TABLE       CREATE TABLE public.requests (
    request_id bigint NOT NULL,
    client_id bigint,
    subject_id bigint,
    description text,
    budget numeric(10,2),
    created_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP,
    selected_response_id bigint
);
    DROP TABLE public.requests;
       public         heap r       postgres    false            �            1259    16438    requests_request_id_seq    SEQUENCE     �   ALTER TABLE public.requests ALTER COLUMN request_id ADD GENERATED ALWAYS AS IDENTITY (
    SEQUENCE NAME public.requests_request_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1
);
            public               postgres    false    226            �            1259    16425 	   responses    TABLE     �   CREATE TABLE public.responses (
    response_id bigint NOT NULL,
    request_id bigint,
    tutor_id bigint,
    message text,
    response_date timestamp without time zone DEFAULT CURRENT_TIMESTAMP
);
    DROP TABLE public.responses;
       public         heap r       postgres    false            �            1259    16424    responses_response_id_seq    SEQUENCE     �   ALTER TABLE public.responses ALTER COLUMN response_id ADD GENERATED ALWAYS AS IDENTITY (
    SEQUENCE NAME public.responses_response_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1
);
            public               postgres    false    224            �            1259    16468    reviews    TABLE     �   CREATE TABLE public.reviews (
    review_id bigint NOT NULL,
    client_id bigint,
    tutor_id bigint,
    review_text text NOT NULL,
    rating numeric(3,2) NOT NULL,
    review_date timestamp without time zone DEFAULT CURRENT_TIMESTAMP
);
    DROP TABLE public.reviews;
       public         heap r       postgres    false            �            1259    16467    reviews_review_id_seq    SEQUENCE     �   ALTER TABLE public.reviews ALTER COLUMN review_id ADD GENERATED ALWAYS AS IDENTITY (
    SEQUENCE NAME public.reviews_review_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1
);
            public               postgres    false    228            �            1259    16487 	   schedules    TABLE     �   CREATE TABLE public.schedules (
    schedule_id bigint NOT NULL,
    tutor_id bigint,
    day_of_week character varying(50) NOT NULL,
    start_time time without time zone NOT NULL,
    end_time time without time zone NOT NULL
);
    DROP TABLE public.schedules;
       public         heap r       postgres    false            �            1259    16486    schedules_schedule_id_seq    SEQUENCE     �   ALTER TABLE public.schedules ALTER COLUMN schedule_id ADD GENERATED ALWAYS AS IDENTITY (
    SEQUENCE NAME public.schedules_schedule_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1
);
            public               postgres    false    230            �            1259    16397    subject    TABLE     �   CREATE TABLE public.subject (
    subject_id bigint NOT NULL,
    subject_name character varying(255) NOT NULL,
    description text
);
    DROP TABLE public.subject;
       public         heap r       postgres    false            �            1259    16396    subject_subject_id_seq    SEQUENCE     �   ALTER TABLE public.subject ALTER COLUMN subject_id ADD GENERATED ALWAYS AS IDENTITY (
    SEQUENCE NAME public.subject_subject_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1
);
            public               postgres    false    220            �            1259    16405    tutors    TABLE       CREATE TABLE public.tutors (
    tutor_id bigint NOT NULL,
    user_id bigint,
    description text,
    rating numeric(3,2) DEFAULT 0.0,
    hourly_rate numeric(10,2) NOT NULL,
    created_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP,
    subject_id bigint
);
    DROP TABLE public.tutors;
       public         heap r       postgres    false            �            1259    16386    users    TABLE     g  CREATE TABLE public.users (
    user_id bigint NOT NULL,
    first_name character varying(255) NOT NULL,
    last_name character varying(255) NOT NULL,
    email character varying(255) NOT NULL,
    password_hash character varying(255) NOT NULL,
    role character varying(50) NOT NULL,
    created_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP
);
    DROP TABLE public.users;
       public         heap r       postgres    false            �            1259    16497    tutorratings    VIEW       CREATE VIEW public.tutorratings AS
 SELECT t.user_id,
    u.first_name,
    u.last_name,
    t.rating,
    t.hourly_rate,
    s.subject_name
   FROM ((public.tutors t
     JOIN public.users u ON ((t.user_id = u.user_id)))
     JOIN public.subject s ON ((t.subject_id = s.subject_id)));
    DROP VIEW public.tutorratings;
       public       v       postgres    false    222    218    218    218    220    220    222    222    222            �            1259    16404    tutors_tutor_id_seq    SEQUENCE     �   ALTER TABLE public.tutors ALTER COLUMN tutor_id ADD GENERATED ALWAYS AS IDENTITY (
    SEQUENCE NAME public.tutors_tutor_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1
);
            public               postgres    false    222            �            1259    16385    users_user_id_seq    SEQUENCE     �   ALTER TABLE public.users ALTER COLUMN user_id ADD GENERATED ALWAYS AS IDENTITY (
    SEQUENCE NAME public.users_user_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1
);
            public               postgres    false    218            k          0    16439    requests 
   TABLE DATA           |   COPY public.requests (request_id, client_id, subject_id, description, budget, created_at, selected_response_id) FROM stdin;
    public               postgres    false    226   GM       i          0    16425 	   responses 
   TABLE DATA           ^   COPY public.responses (response_id, request_id, tutor_id, message, response_date) FROM stdin;
    public               postgres    false    224   �M       m          0    16468    reviews 
   TABLE DATA           c   COPY public.reviews (review_id, client_id, tutor_id, review_text, rating, review_date) FROM stdin;
    public               postgres    false    228   -N       o          0    16487 	   schedules 
   TABLE DATA           ]   COPY public.schedules (schedule_id, tutor_id, day_of_week, start_time, end_time) FROM stdin;
    public               postgres    false    230   �N       e          0    16397    subject 
   TABLE DATA           H   COPY public.subject (subject_id, subject_name, description) FROM stdin;
    public               postgres    false    220   �N       g          0    16405    tutors 
   TABLE DATA           m   COPY public.tutors (tutor_id, user_id, description, rating, hourly_rate, created_at, subject_id) FROM stdin;
    public               postgres    false    222   kP       c          0    16386    users 
   TABLE DATA           g   COPY public.users (user_id, first_name, last_name, email, password_hash, role, created_at) FROM stdin;
    public               postgres    false    218   �P       v           0    0    requests_request_id_seq    SEQUENCE SET     E   SELECT pg_catalog.setval('public.requests_request_id_seq', 2, true);
          public               postgres    false    225            w           0    0    responses_response_id_seq    SEQUENCE SET     G   SELECT pg_catalog.setval('public.responses_response_id_seq', 1, true);
          public               postgres    false    223            x           0    0    reviews_review_id_seq    SEQUENCE SET     C   SELECT pg_catalog.setval('public.reviews_review_id_seq', 1, true);
          public               postgres    false    227            y           0    0    schedules_schedule_id_seq    SEQUENCE SET     G   SELECT pg_catalog.setval('public.schedules_schedule_id_seq', 1, true);
          public               postgres    false    229            z           0    0    subject_subject_id_seq    SEQUENCE SET     E   SELECT pg_catalog.setval('public.subject_subject_id_seq', 10, true);
          public               postgres    false    219            {           0    0    tutors_tutor_id_seq    SEQUENCE SET     A   SELECT pg_catalog.setval('public.tutors_tutor_id_seq', 1, true);
          public               postgres    false    221            |           0    0    users_user_id_seq    SEQUENCE SET     ?   SELECT pg_catalog.setval('public.users_user_id_seq', 3, true);
          public               postgres    false    217            �           2606    16446    requests requests_pkey 
   CONSTRAINT     \   ALTER TABLE ONLY public.requests
    ADD CONSTRAINT requests_pkey PRIMARY KEY (request_id);
 @   ALTER TABLE ONLY public.requests DROP CONSTRAINT requests_pkey;
       public                 postgres    false    226            �           2606    16432    responses responses_pkey 
   CONSTRAINT     _   ALTER TABLE ONLY public.responses
    ADD CONSTRAINT responses_pkey PRIMARY KEY (response_id);
 B   ALTER TABLE ONLY public.responses DROP CONSTRAINT responses_pkey;
       public                 postgres    false    224            �           2606    16475    reviews reviews_pkey 
   CONSTRAINT     Y   ALTER TABLE ONLY public.reviews
    ADD CONSTRAINT reviews_pkey PRIMARY KEY (review_id);
 >   ALTER TABLE ONLY public.reviews DROP CONSTRAINT reviews_pkey;
       public                 postgres    false    228            �           2606    16491    schedules schedules_pkey 
   CONSTRAINT     _   ALTER TABLE ONLY public.schedules
    ADD CONSTRAINT schedules_pkey PRIMARY KEY (schedule_id);
 B   ALTER TABLE ONLY public.schedules DROP CONSTRAINT schedules_pkey;
       public                 postgres    false    230            �           2606    16403    subject subject_pkey 
   CONSTRAINT     Z   ALTER TABLE ONLY public.subject
    ADD CONSTRAINT subject_pkey PRIMARY KEY (subject_id);
 >   ALTER TABLE ONLY public.subject DROP CONSTRAINT subject_pkey;
       public                 postgres    false    220            �           2606    16413    tutors tutors_pkey 
   CONSTRAINT     V   ALTER TABLE ONLY public.tutors
    ADD CONSTRAINT tutors_pkey PRIMARY KEY (tutor_id);
 <   ALTER TABLE ONLY public.tutors DROP CONSTRAINT tutors_pkey;
       public                 postgres    false    222            �           2606    16395    users users_email_key 
   CONSTRAINT     Q   ALTER TABLE ONLY public.users
    ADD CONSTRAINT users_email_key UNIQUE (email);
 ?   ALTER TABLE ONLY public.users DROP CONSTRAINT users_email_key;
       public                 postgres    false    218            �           2606    16393    users users_pkey 
   CONSTRAINT     S   ALTER TABLE ONLY public.users
    ADD CONSTRAINT users_pkey PRIMARY KEY (user_id);
 :   ALTER TABLE ONLY public.users DROP CONSTRAINT users_pkey;
       public                 postgres    false    218            �           2620    16503 #   reviews update_tutor_rating_trigger    TRIGGER     �   CREATE TRIGGER update_tutor_rating_trigger AFTER INSERT OR UPDATE ON public.reviews FOR EACH ROW EXECUTE FUNCTION public.update_tutor_rating_after_review();
 <   DROP TRIGGER update_tutor_rating_trigger ON public.reviews;
       public               postgres    false    232    228            �           2606    16462    responses fk_request    FK CONSTRAINT     �   ALTER TABLE ONLY public.responses
    ADD CONSTRAINT fk_request FOREIGN KEY (request_id) REFERENCES public.requests(request_id);
 >   ALTER TABLE ONLY public.responses DROP CONSTRAINT fk_request;
       public               postgres    false    226    3264    224            �           2606    16447     requests requests_client_id_fkey    FK CONSTRAINT     �   ALTER TABLE ONLY public.requests
    ADD CONSTRAINT requests_client_id_fkey FOREIGN KEY (client_id) REFERENCES public.users(user_id);
 J   ALTER TABLE ONLY public.requests DROP CONSTRAINT requests_client_id_fkey;
       public               postgres    false    226    3256    218            �           2606    16457 +   requests requests_selected_response_id_fkey    FK CONSTRAINT     �   ALTER TABLE ONLY public.requests
    ADD CONSTRAINT requests_selected_response_id_fkey FOREIGN KEY (selected_response_id) REFERENCES public.responses(response_id);
 U   ALTER TABLE ONLY public.requests DROP CONSTRAINT requests_selected_response_id_fkey;
       public               postgres    false    3262    226    224            �           2606    16452 !   requests requests_subject_id_fkey    FK CONSTRAINT     �   ALTER TABLE ONLY public.requests
    ADD CONSTRAINT requests_subject_id_fkey FOREIGN KEY (subject_id) REFERENCES public.subject(subject_id);
 K   ALTER TABLE ONLY public.requests DROP CONSTRAINT requests_subject_id_fkey;
       public               postgres    false    226    220    3258            �           2606    16433 !   responses responses_tutor_id_fkey    FK CONSTRAINT     �   ALTER TABLE ONLY public.responses
    ADD CONSTRAINT responses_tutor_id_fkey FOREIGN KEY (tutor_id) REFERENCES public.tutors(tutor_id);
 K   ALTER TABLE ONLY public.responses DROP CONSTRAINT responses_tutor_id_fkey;
       public               postgres    false    222    3260    224            �           2606    16476    reviews reviews_client_id_fkey    FK CONSTRAINT     �   ALTER TABLE ONLY public.reviews
    ADD CONSTRAINT reviews_client_id_fkey FOREIGN KEY (client_id) REFERENCES public.users(user_id) ON DELETE CASCADE;
 H   ALTER TABLE ONLY public.reviews DROP CONSTRAINT reviews_client_id_fkey;
       public               postgres    false    228    3256    218            �           2606    16481    reviews reviews_tutor_id_fkey    FK CONSTRAINT     �   ALTER TABLE ONLY public.reviews
    ADD CONSTRAINT reviews_tutor_id_fkey FOREIGN KEY (tutor_id) REFERENCES public.tutors(tutor_id) ON DELETE CASCADE;
 G   ALTER TABLE ONLY public.reviews DROP CONSTRAINT reviews_tutor_id_fkey;
       public               postgres    false    222    228    3260            �           2606    16492 !   schedules schedules_tutor_id_fkey    FK CONSTRAINT     �   ALTER TABLE ONLY public.schedules
    ADD CONSTRAINT schedules_tutor_id_fkey FOREIGN KEY (tutor_id) REFERENCES public.tutors(tutor_id) ON DELETE CASCADE;
 K   ALTER TABLE ONLY public.schedules DROP CONSTRAINT schedules_tutor_id_fkey;
       public               postgres    false    230    222    3260            �           2606    16419    tutors tutors_subject_id_fkey    FK CONSTRAINT     �   ALTER TABLE ONLY public.tutors
    ADD CONSTRAINT tutors_subject_id_fkey FOREIGN KEY (subject_id) REFERENCES public.subject(subject_id) ON DELETE SET NULL;
 G   ALTER TABLE ONLY public.tutors DROP CONSTRAINT tutors_subject_id_fkey;
       public               postgres    false    222    3258    220            �           2606    16414    tutors tutors_user_id_fkey    FK CONSTRAINT     �   ALTER TABLE ONLY public.tutors
    ADD CONSTRAINT tutors_user_id_fkey FOREIGN KEY (user_id) REFERENCES public.users(user_id) ON DELETE CASCADE;
 D   ALTER TABLE ONLY public.tutors DROP CONSTRAINT tutors_user_id_fkey;
       public               postgres    false    222    3256    218            k   f   x�-��� ��0 �Q"C8���]gpb4bt��Fr0=�)*`Ń;b�U��lHyRx�(��8~_H8�ւ�5����+�sp.�7-u��b��`��,�      i   `   x�U��	�0߹*����b���c!A%�5�ud�����N6��la�6#���,cŎl�-�T���VC-Z�g�!������BcCDh�0       m   O   x�3�4��.6^l���¦�/�_�S����~���&ENS=N##]C#]Cc##++S=KSS�=... ��;      o   (   x�3�4����KI��40�25�20�4��212�b���� ���      e   �  x�u�[N�@E�gV1+@�7{a1��Z(��@|�'RH�4�n���vR
-R��d|���n���<��*}洤��+�������d3"���g���k��"<�u��a�m���	�A�j�r��\p�d�'���5 ���ޱ�(����xl�����RA����X/*���{,�2�s#>Q�Ci��ࡦ�9���Sɽ���G<�A�>v� ���R�N��:Y�E�|�B��҅T/��*[Q�O��>�o4rV�au5A�Ju=5C O(�����@C5�0�ti�XnEYnv��6R�<st��\�TX��Z2�}���Ox�z+��,җ�*�ۘB.�V�/��%�0�k+�XfG�>��X�mF+(�|۹ J��w�as�;�����46�����m�W
^�+���� 9n�      g   h   x�-��	�0F�<�2@��شd�c�����5%]��Fu������p0����o���/�`������߆�:Q�"���]K�ڬ���V՘r~<�4l1���82M      c   �  x�u��jU1���>����ef23I�J�֢`EQ$�$�ۣ�����'�!| ���3���Qqa��$�����a~7�?�_������0��/{�������qh��zZ��4Mus�$�7���ᬜ^�܎���1���w�\�>8��99>���d%�Z��;��Efi @!�d��A\�a�%�@ ���/.K!a_����j��Ēs�DhQ��%I�d�/9�fC٬��w�v�� F�{@�]c��~9���|{�}q�����p��ƃ�[�׻�TPbQ�5zP�)c�FQ(k����"�Ť:�R�jJ��2�DUx���M"��؟l�Y�j�]����Fï�׉q�
�C�nHv�����ګ�{����{�9h���!f4�|�Xci.X�sP�"֜��n1d(֝:	�+���M�ݣ�,I��ꎭ*�#��o����Z	r� ��N���z��>��x�Z,? �ڃ     