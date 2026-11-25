const fastify = require('fastify')({ logger: true });
const { Pool } = require('pg');

const timeout = Number(process.env.PG_TIMEOUT_MS);
const pool = new Pool({
  connectionTimeoutMillis: timeout,
  statement_timeout: timeout,
  query_timeout: timeout,
});

pool.on('error', (err) => {
  fastify.log.warn({ err }, 'Idle database connection failed');
});

fastify.get('/health', async () => ({ status: 'ok' }));

fastify.get('/inventory/1', async (request, reply) => {
  let result;
  try {
    result = await pool.query(
      'SELECT product_id, quantity FROM inventory WHERE product_id = $1',
      [1],
    );
  } catch (err) {
    request.log.warn({ err, databaseHost: process.env.PGHOST }, 'Inventory query failed');
    return reply.code(503).send({ error: 'Inventory database unavailable' });
  }

  if (result.rowCount === 0) {
    return reply.code(404).send({ error: 'Product not found' });
  }

  return result.rows[0];
});

fastify.addHook('onClose', async () => {
  await pool.end();
});

fastify.listen({ host: '0.0.0.0', port: 3000 }).catch((err) => {
  fastify.log.error(err);
  process.exit(1);
});
