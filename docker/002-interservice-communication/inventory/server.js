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

const inventoryRouteOptions = {
  schema: {
    params: {
      type: 'object',
      required: ['id'],
      properties: {
        id: { type: 'string', pattern: '^0*[1-9][0-9]*$' },
      },
    },
  },
  attachValidation: true,
};

fastify.get('/inventory/:id', inventoryRouteOptions, async (request, reply) => {
  if (request.validationError) {
    request.log.warn(
      { err: request.validationError, databaseHost: process.env.PGHOST },
      'Invalid parameter',
    );
    return reply.code(400).send({ error: 'Invalid parameter' });
  }

  const { id } = request.params;
  const productId = BigInt(id);
  // IDs above the PostgreSQL integer range cannot match a product.
  if (productId > 2147483647n) {
    return reply.code(404).send({ error: 'Product not found' });
  }

  let result;
  try {
    result = await pool.query(
      'SELECT product_id, quantity FROM inventory WHERE product_id = $1',
      [Number(productId)],
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
