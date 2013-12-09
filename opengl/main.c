


int main()
{
	int terminate = 0;
	GLfloat cx, cy;
	bcm_host_init();
	
	//clear application state
	memset( state, 0, siseof( *state) );
	init_ogl(state);
	init_shaders(state);
	
}