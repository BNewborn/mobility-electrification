### 07_CommutingDistance_CentroidToCentroid

##### 1. upload shp file to PostgreSQL (run the 4-row codes in terminal)

   ```
   shp2pgsql -s 102003 -c -W "GBK" ipums_puma_2010.shp ipums.ipums_puma_2010 > /Users/jingrong/Desktop/tecnyc/sql/ipums_puma_2010.sql
   psql -h localhost -p 5432 -U postgres -d tecnyc -f /Users/jingrong/Desktop/tecnyc/sql/ipums_puma_2010.sql
   shp2pgsql -s 102003 -c -W "GBK" ipums_migpuma_pwpuma_2010.shp ipums.ipums_migpuma_pwpuma_2010 > /Users/jingrong/Desktop/tecnyc/sql/ipums_migpuma_pwpuma_2010.sql
   psql -h localhost -p 5432 -U postgres -d tecnyc -f /Users/jingrong/Desktop/tecnyc/sql/ipums_migpuma_pwpuma_2010.sql
   ```



##### 2. filter the nine states, and rename the puma key

```sql
DROP TABLE IF EXISTS ipums.puma_work; CREATE TABLE ipums.puma_work AS SELECT statefip, state, pwpuma, concat(statefip,'_',pwpuma) AS "PUMAKEY_WORK", geom FROM ipums_migpuma_pwpuma_2010 WHERE statefip IN ('34','36','42','09','25','44','33','50','23');
DROP TABLE IF EXISTS ipums.puma_home; CREATE TABLE ipums.puma_home AS SELECT statefip, state, puma, concat(statefip,'_',puma) AS "PUMAKEY_HOME", geom FROM ipums_puma_2010 WHERE statefip IN ('34','36','42','09','25','44','33','50','23');
ALTER TABLE ipums.puma_work ALTER COLUMN geom TYPE geometry(MultiPolygon, 4326) USING ST_Transform(ST_SetSRID(geom,102003),4326);
ALTER TABLE ipums.puma_home ALTER COLUMN geom TYPE geometry(MultiPolygon, 4326) USING ST_Transform(ST_SetSRID(geom,102003),4326);
```



##### 3. centroid_to_centroid distance calculation

*IN & INSIDE commuters: PUMA_HOME (419) - PUMA_WORK (Manhattan 36_03800)
OUT commuters: PUMA_HOME (Manhattan 36_038%, 10) - PUMA_WORK (other than Manhattan 36_03800, 126-1=125)*

```sql
DROP TABLE IF EXISTS ipums.puma_distance_centroid; CREATE TABLE ipums.puma_distance_centroid AS 
WITH in_inside AS (
		SELECT "PUMAKEY_HOME", "PUMAKEY_WORK", 
		ST_Distance(ST_Transform(ST_Centroid(puma_home.geom),3857),ST_Transform(ST_Centroid(puma_work.geom),3857))/1000 AS "DISTANCE_KM" 
		FROM puma_home, puma_work WHERE "PUMAKEY_WORK"='36_03800'),
out_ AS (
		SELECT "PUMAKEY_HOME", "PUMAKEY_WORK", 
		ST_Distance(ST_Transform(ST_Centroid(puma_home.geom),3857),ST_Transform(ST_Centroid(puma_work.geom),3857))/1000 AS "DISTANCE_KM" 
		FROM puma_home, puma_work WHERE "PUMAKEY_HOME" LIKE '36_038%' AND "PUMAKEY_WORK" <> '36_03800')
SELECT * FROM in_inside UNION SELECT * FROM out_ ORDER BY "PUMAKEY_WORK", "PUMAKEY_HOME"
```

