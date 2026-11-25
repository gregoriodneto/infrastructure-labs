CREATE TABLE inventory (
    product_id integer PRIMARY KEY,
    quantity integer NOT NULL CHECK (quantity >= 0)
);

INSERT INTO inventory (product_id, quantity) VALUES (1, 12), (2, 0);
