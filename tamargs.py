from Compiler.library import print_ln 
from Compiler.types import Matrix, Array, sint
from Compiler.compilerLib import Compiler
from Compiler.program import Program, defaults
import sys

#opts = defaults()
#opts.ring = 64
#opts.edabit = True
#prog = Program(['filteredSum'], opts)

usage = "usage: %prog [options] [args]"
compiler = Compiler(usage=usage)
compiler.parser.add_option("--rows", dest="rows")
compiler.parser.add_option("--columns", dest="columns")
compiler.parser.add_option("--filters", dest="filters")
compiler.parser.add_option("--types", dest="types")
compiler.parser.add_option("--parties", dest="parties")
compiler.parse_args()
if not compiler.options.rows:
    compiler.parser.error("--rows required")
if not compiler.options.columns:
    compiler.parser.error("--columns required")
if not compiler.options.filters:
    compiler.parser.error("--filters required")

if not all( f in ['>','<','='] for f in compiler.options.filters ):
	print( f"Error: invalid filter" )
	print( compiler.options.filters )
	sys.exit(1)

@compiler.register_function('filteredSum')
def fs():
	nParties = 3
	nRows = int(compiler.options.rows)
	nCols = int(compiler.options.columns)
	nParties = int(compiler.options.parties)
	filters = str(compiler.options.filters)
	if compiler.options.parties:
		nParties = int(compiler.options.parties)
	if len(filters) < nCols-1:
		print( "Error: Too few filters" )
		print( f"nCols = {nCols}, len(filters) = {len(filters)}" )
	if len(filters) > nCols-1:
		print( "Error: Too many filters" )
		print( f"nCols = {nCols}, len(filters) = {len(filters)}" )

	A = [ Matrix( nRows, nCols, sint ) for _ in range(nParties) ]
	FF = [ Array( nCols-1, sint) for _ in range(nParties) ]

	for p in range(nParties):
		FF[p].input_from(p)
		A[p].input_from(p)

	####################################
	# Reconstruct shares
	####################################

	C = sum( A[p] for p in range(nParties) )
	F = sum( FF[p] for p in range(nParties) )

	####################################
	# Compute filtered sum
	####################################

	M = sint.Matrix( nRows, 1 )
	M.assign_all(1)

	for j in range(nCols-1):
		CM = sint.Matrix( nRows, 1 )
		if filters[j] == "<":
			CM.assign( C.get_column(j+1) < F[j] )
		if filters[j] == ">":
			CM.assign( C.get_column(j+1) > F[j] )
		if filters[j] == "=":
			CM.assign( C.get_column(j+1) == F[j] )
		M = M.schur( CM )
		assert M.sizes == (nRows,1)

	FC = sint.Matrix( 1, nRows )
	FC.assign( C.get_column(0) )
	FS = FC.dot(M)
	assert FS.sizes == (1,1)

	for i in range( min(nRows,10) ):
		print_ln( "C[%s][0] = %s, C[%s][1] = %s, M[%s] = %s, F[1] = %s", i, C[i][0].reveal(), i, C[i][1].reveal(), i, M[i].reveal(), F[1].reveal() )

	print_ln( "Filtered sum = %s", FS[0][0].reveal() )

if __name__ == "__main__":
	compiler.compile_func()
