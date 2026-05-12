CREATE EXTENSION IF NOT EXISTS postgis;

CREATE TABLE IF NOT EXISTS properties (
    id SERIAL PRIMARY KEY,
    title VARCHAR(255) NOT NULL,
    address_clean VARCHAR(255) NOT NULL,
    price NUMERIC,      
    area NUMERIC,          
    rooms INTEGER,
    geom GEOMETRY(Point, 4326),
    link TEXT UNIQUE,      
    scraped_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS points_of_interest (
    id SERIAL PRIMARY KEY,
    osm_id BIGINT UNIQUE,       
    category VARCHAR(50),    
    name VARCHAR(255),
    geom GEOMETRY(Point, 4326) 
);

CREATE INDEX properties_geom_idx ON properties USING GIST (geom);
CREATE INDEX poi_geom_idx ON points_of_interest USING GIST (geom);