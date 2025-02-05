pkgdatadir = get_option('prefix') / get_option('datadir') / meson.project_name()
moduledir = pkgdatadir / 'realms'
gnome = import('gnome')

gnome.compile_resources('realms',
  'realms.gresource.xml',
  gresource_bundle: true,
  install: true,
  install_dir: pkgdatadir,
)

python = import('python')

conf = configuration_data()
conf.set('PYTHON', python.find_installation('python3').full_path())
conf.set('VERSION', meson.project_version())
conf.set('localedir', get_option('prefix') / get_option('localedir'))
conf.set('pkgdatadir', pkgdatadir)

configure_file(
  input: 'realms.in',
  output: 'realms',
  configuration: conf,
  install: true,
  install_dir: get_option('bindir'),
  install_mode: 'r-xr-xr-x'
)

configure_file(
  input: 'config.in',
  output: 'config.py',
  configuration: conf,
  install: true,
  install_dir: get_option('bindir'),
  install_mode: 'r-xr-xr-x'
)

realms_sources = [
  '__init__.py',
  'main.py',
]

install_data(realms_sources, install_dir: moduledir)
install_subdir('helpers', install_dir: moduledir)
install_subdir('libvirt_wrap', install_dir: moduledir)
install_subdir('ui', install_dir: moduledir)
install_subdir('templates', install_dir: moduledir)